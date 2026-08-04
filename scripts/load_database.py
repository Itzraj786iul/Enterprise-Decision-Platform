#!/usr/bin/env python3
"""
Production OLTP CSV → PostgreSQL loader for the Enterprise Decision Platform.

Uses PostgreSQL COPY (psycopg3) for bulk load. Does not modify analytics,
APIs, frontend, or synthetic data generation.

Usage (from repository root):
  set DATABASE_URL=postgresql://...@...neon.tech/db?sslmode=require
  python scripts/load_database.py --data-dir "E:/Conulsting project/data/generated"

  python scripts/load_database.py --dry-run --verbose
  python scripts/load_database.py --truncate
  python scripts/load_database.py   # resume from data/generated/_load_state.json
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Force UTF-8 stdio on Windows so progress/log characters do not crash the load.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except Exception:  # noqa: BLE001
    pass

# PostgreSQL integer families (information_schema.data_type / udt_name).
INTEGER_UDT_NAMES = frozenset({"int2", "int4", "int8", "smallint", "integer", "bigint"})
INTEGER_DATA_TYPES = frozenset({"smallint", "integer", "bigint"})

NULL_TOKENS = frozenset(
    {
        "",
        "nan",
        "NaN",
        "NAN",
        "<NA>",
        "None",
        "none",
        "NULL",
        "null",
        "NaT",
        "#N/A",
        "n/a",
        "N/A",
    }
)

# COPY stream batching (rows / bytes) — keeps memory bounded on large CSVs.
COPY_FLUSH_ROWS = 5_000
COPY_FLUSH_BYTES = 1_048_576

_COPY_CONTEXT_RE = re.compile(
    r'COPY\s+(?P<table>\w+)\s*,\s*line\s+(?P<line>\d+)\s*,\s*column\s+(?P<column>\w+)\s*:\s*"(?P<value>.*)"',
    re.IGNORECASE | re.DOTALL,
)
_COPY_CONTEXT_LOOSE_RE = re.compile(
    r"line\s+(?P<line>\d+).*?column\s+(?P<column>\w+).*?(?:\"(?P<value>.*?)\"|(?P<value2>\S+))",
    re.IGNORECASE | re.DOTALL,
)

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "generated"
DEFAULT_SCHEMA = "oltp"
STATE_FILENAME = "_load_state.json"

# FK-safe load order for database/schema.sql (oltp).
# product_categories is self-referential; generator writes parents before children.
LOAD_ORDER: tuple[str, ...] = (
    "calendar_date",
    "regions",
    "channels",
    "payment_methods",
    "distribution_centers",
    "stores",
    "product_categories",
    "suppliers",
    "customers",
    "loyalty_accounts",
    "customer_addresses",
    "products",
    "product_suppliers",
    "price_history",
    "cost_history",
    "employees",
    "promotions",
    "marketing_campaigns",
    "orders",
    "order_items",
    "order_item_promotions",
    "payments",
    "shipments",
    "shipment_items",
    "returns",
    "return_items",
    "campaign_responses",
    "inventory",
    "inventory_transactions",
    "inventory_snapshots",
    "purchase_orders",
    "purchase_order_items",
    "goods_receipts",
    "goods_receipt_items",
    "store_labor_hours",
)

# Truncate / dependency-safe reverse order (children first).
TRUNCATE_ORDER: tuple[str, ...] = tuple(reversed(LOAD_ORDER))


# -----------------------------------------------------------------------------
# Data classes
# -----------------------------------------------------------------------------
@dataclass
class TableResult:
    table: str
    status: str  # loaded | skipped_resume | skipped_missing | dry_run | failed
    csv_rows: int | None = None
    db_rows: int | None = None
    duration_sec: float | None = None
    message: str = ""


@dataclass
class LoadSummary:
    started_at: str
    finished_at: str | None = None
    data_dir: str = ""
    schema: str = DEFAULT_SCHEMA
    tables_loaded: int = 0
    tables_skipped: int = 0
    tables_missing: int = 0
    tables_failed: int = 0
    rows_loaded: int = 0
    duration_sec: float = 0.0
    results: list[TableResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            **{k: v for k, v in asdict(self).items() if k != "results"},
            "results": [asdict(r) for r in self.results],
        }


# -----------------------------------------------------------------------------
# URL / connection helpers
# -----------------------------------------------------------------------------
def normalize_psycopg_url(url: str) -> str:
    """Normalize DATABASE_URL for psycopg3 (not SQLAlchemy dialect form)."""
    raw = (url or "").strip()
    if not raw:
        raise ValueError("DATABASE_URL is empty")

    lowered = raw.lower()
    for prefix in (
        "postgresql+psycopg://",
        "postgresql+psycopg2://",
        "postgres://",
    ):
        if lowered.startswith(prefix):
            raw = "postgresql://" + raw[len(prefix) :]
            lowered = raw.lower()
            break

    parts = urlsplit(raw)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    host = (parts.hostname or "").lower()
    if host.endswith(".neon.tech") or "neon.tech" in host:
        query.setdefault("sslmode", "require")
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def connect(database_url: str):
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "psycopg is required. Install with: python -m pip install 'psycopg[binary]'"
        ) from exc
    return psycopg.connect(normalize_psycopg_url(database_url), autocommit=False)


# -----------------------------------------------------------------------------
# Filesystem helpers
# -----------------------------------------------------------------------------
def resolve_data_dir(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_dir():
            raise SystemExit(f"--data-dir not found or not a directory: {path}")
        return path

    default = DEFAULT_DATA_DIR
    if default.is_dir():
        return default.resolve()

    raise SystemExit(
        f"Default data directory not found: {default}\n"
        f"Generate data first or pass --data-dir PATH"
    )


def csv_path_for(data_dir: Path, table: str) -> Path:
    return data_dir / f"{table}.csv"


def read_csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
    if not header:
        raise ValueError(f"CSV has no header: {path}")
    return [c.strip() for c in header]


def count_csv_data_rows(path: Path) -> int:
    """Count data rows (excludes header). Streams the file."""
    with path.open("rb") as fh:
        # Skip header
        if not fh.readline():
            return 0
        return sum(1 for _ in fh)


def discover_extra_csvs(data_dir: Path) -> list[str]:
    known = set(LOAD_ORDER)
    extras: list[str] = []
    for path in sorted(data_dir.glob("*.csv")):
        name = path.stem
        if name not in known:
            extras.append(name)
    return extras


# -----------------------------------------------------------------------------
# Resume state
# -----------------------------------------------------------------------------
def state_path(data_dir: Path) -> Path:
    return data_dir / STATE_FILENAME


def load_state(data_dir: Path) -> dict[str, Any]:
    path = state_path(data_dir)
    if not path.exists():
        return {"completed": {}, "version": 1}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"completed": {}, "version": 1}
    if not isinstance(payload.get("completed"), dict):
        payload["completed"] = {}
    return payload


def save_state(data_dir: Path, state: dict[str, Any]) -> None:
    path = state_path(data_dir)
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def clear_state(data_dir: Path) -> None:
    path = state_path(data_dir)
    if path.exists():
        path.unlink()


# -----------------------------------------------------------------------------
# Progress
# -----------------------------------------------------------------------------
class ProgressBar:
    """Minimal dependency-free progress bar."""

    def __init__(self, total: int, *, desc: str = "", enabled: bool = True) -> None:
        self.total = max(total, 1)
        self.desc = desc
        self.enabled = enabled and sys.stderr.isatty()
        self.n = 0
        self._last_len = 0

    def update(self, n: int = 1) -> None:
        self.n = min(self.n + n, self.total)
        if not self.enabled:
            return
        width = 28
        filled = int(width * self.n / self.total)
        bar = "#" * filled + "-" * (width - filled)
        pct = 100.0 * self.n / self.total
        line = f"\r{self.desc} [{bar}] {self.n}/{self.total} ({pct:5.1f}%)"
        pad = max(0, self._last_len - len(line))
        sys.stderr.write(line + (" " * pad))
        sys.stderr.flush()
        self._last_len = len(line)

    def close(self) -> None:
        if self.enabled:
            sys.stderr.write("\n")
            sys.stderr.flush()


# -----------------------------------------------------------------------------
# Database operations
# -----------------------------------------------------------------------------
def qualify(schema: str, table: str) -> str:
    return f"{_ident(schema)}.{_ident(table)}"


def _ident(name: str) -> str:
    if not name.replace("_", "").isalnum():
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return f'"{name}"'


def table_exists(conn, schema: str, table: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
            """,
            (schema, table),
        )
        return cur.fetchone() is not None


def count_table_rows(conn, schema: str, table: str) -> int:
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {qualify(schema, table)}")
        row = cur.fetchone()
        return int(row[0]) if row else 0


def primary_key_columns(conn, schema: str, table: str) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema = %s
              AND tc.table_name = %s
              AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY kcu.ordinal_position
            """,
            (schema, table),
        )
        return [r[0] for r in cur.fetchall()]


def sync_identity_sequence(conn, schema: str, table: str) -> None:
    """Advance identity/serial sequence after COPY with explicit PKs."""
    pks = primary_key_columns(conn, schema, table)
    if len(pks) != 1:
        return
    pk = pks[0]
    qtable = qualify(schema, table)
    with conn.cursor() as cur:
        cur.execute("SELECT pg_get_serial_sequence(%s, %s)", (f"{schema}.{table}", pk))
        seq_row = cur.fetchone()
        if not seq_row or not seq_row[0]:
            return
        seq_name = seq_row[0]
        cur.execute(f"SELECT COALESCE(MAX({_ident(pk)}), 0) FROM {qtable}")
        max_id = int(cur.fetchone()[0])
        if max_id <= 0:
            return
        cur.execute("SELECT setval(%s, %s, true)", (seq_name, max_id))


def truncate_tables(conn, schema: str, tables: Sequence[str], *, verbose: bool) -> None:
    existing = [t for t in tables if table_exists(conn, schema, t)]
    if not existing:
        return
    # Single statement with CASCADE handles FK graph safely.
    targets = ", ".join(qualify(schema, t) for t in existing)
    sql = f"TRUNCATE TABLE {targets} RESTART IDENTITY CASCADE"
    if verbose:
        print(f"[truncate] {sql}", flush=True)
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def fetch_column_types(conn, schema: str, table: str) -> dict[str, str]:
    """Return {column_name: udt_name} for a table."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name, udt_name, data_type
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            """,
            (schema, table),
        )
        out: dict[str, str] = {}
        for name, udt, data_type in cur.fetchall():
            out[name] = (udt or data_type or "").lower()
        return out


def integer_column_indexes(
    columns: Sequence[str],
    column_types: dict[str, str],
) -> set[int]:
    indexes: set[int] = set()
    for i, col in enumerate(columns):
        udt = column_types.get(col, "")
        data_type = udt  # udt_name already preferred
        if udt in INTEGER_UDT_NAMES or data_type in INTEGER_DATA_TYPES:
            indexes.add(i)
    return indexes


def is_null_like(value: str | None) -> bool:
    if value is None:
        return True
    s = value.strip()
    if s in NULL_TOKENS:
        return True
    # pandas sometimes emits bare whitespace
    return s == ""


def normalize_integer_cell(raw: str) -> str:
    """
    Convert pandas-style integer floats (1.0) to integer text (1).
    NULL-like → '' (COPY NULL '').
    Non-integral floats left unchanged so PostgreSQL reports a clear error.
    """
    if is_null_like(raw):
        return ""
    s = raw.strip()
    # Fast path: already a plain integer string
    if re.fullmatch(r"-?\d+", s):
        return s
    try:
        f = float(s)
    except ValueError:
        return s
    if f != f:  # NaN
        return ""
    if f.is_integer():
        return str(int(f))
    return s


def normalize_cell(raw: str | None, *, is_integer: bool) -> str:
    if is_null_like(raw):
        return ""
    assert raw is not None
    if is_integer:
        return normalize_integer_cell(raw)
    # Non-integer: still coerce null tokens; keep other values as-is
    if raw.strip() in NULL_TOKENS:
        return ""
    return raw


def normalize_row(row: Sequence[str], integer_indexes: set[int]) -> list[str]:
    out: list[str] = []
    for i, cell in enumerate(row):
        out.append(normalize_cell(cell, is_integer=(i in integer_indexes)))
    # Pad / trim to header width callers already enforce via csv reader
    return out


def format_copy_error(exc: BaseException, *, table: str) -> str:
    """Extract table / column / line / value from PostgreSQL COPY errors when present."""
    text = str(exc)
    # psycopg may nest diagnostics
    diag = getattr(exc, "diag", None)
    if diag is not None:
        parts = [getattr(diag, attr, None) for attr in ("message_primary", "message_detail", "context")]
        text = "\n".join(p for p in parts if p) or text

    match = _COPY_CONTEXT_RE.search(text) or _COPY_CONTEXT_LOOSE_RE.search(text)
    if match:
        gd = match.groupdict()
        line = gd.get("line")
        column = gd.get("column")
        value = gd.get("value") or gd.get("value2") or ""
        return (
            f"table={table} column={column} line={line} value={value!r}\n"
            f"detail={text.strip()}"
        )
    return f"table={table}\ndetail={text.strip()}"


def copy_csv_into_table(
    conn,
    *,
    schema: str,
    table: str,
    path: Path,
    columns: Sequence[str],
    verbose: bool,
) -> None:
    """
    Stream CSV → in-memory normalize (integer floats / null tokens) → COPY FROM STDIN.

    Original CSV files on disk are never modified.
    """
    column_types = fetch_column_types(conn, schema, table)
    int_indexes = integer_column_indexes(columns, column_types)
    missing = [c for c in columns if c not in column_types]
    if missing:
        raise ValueError(
            f"CSV columns not found on {schema}.{table}: {', '.join(missing)}"
        )

    col_list = ", ".join(_ident(c) for c in columns)
    sql = (
        f"COPY {qualify(schema, table)} ({col_list}) "
        f"FROM STDIN WITH (FORMAT csv, HEADER true, NULL '')"
    )
    if verbose:
        print(
            f"[copy] {table} <- {path.name} "
            f"({len(columns)} cols, {len(int_indexes)} integer normalized)",
            flush=True,
        )

    with conn.cursor() as cur:
        with path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            if header is None:
                raise ValueError(f"CSV has no header: {path}")
            header = [c.strip() for c in header]
            if header != list(columns):
                # columns arg came from same file; tolerate BOM on first name
                if [c.lstrip("\ufeff") for c in header] != list(columns):
                    raise ValueError(f"CSV header mismatch for {table}")

            with cur.copy(sql) as copy:
                buf = io.StringIO()
                writer = csv.writer(buf, lineterminator="\n")
                writer.writerow(columns)
                rows_buffered = 0

                def flush() -> None:
                    nonlocal rows_buffered
                    payload = buf.getvalue()
                    if payload:
                        copy.write(payload)
                    buf.seek(0)
                    buf.truncate(0)
                    rows_buffered = 0

                for row in reader:
                    if len(row) < len(columns):
                        row = list(row) + [""] * (len(columns) - len(row))
                    elif len(row) > len(columns):
                        row = list(row[: len(columns)])
                    writer.writerow(normalize_row(row, int_indexes))
                    rows_buffered += 1
                    if rows_buffered >= COPY_FLUSH_ROWS or buf.tell() >= COPY_FLUSH_BYTES:
                        flush()
                flush()


# -----------------------------------------------------------------------------
# Core load
# -----------------------------------------------------------------------------
def load_one_table(
    conn,
    *,
    schema: str,
    table: str,
    path: Path,
    truncate_each: bool,
    dry_run: bool,
    verbose: bool,
) -> TableResult:
    t0 = time.perf_counter()
    csv_rows = count_csv_data_rows(path)
    columns = read_csv_header(path)

    if dry_run:
        exists = table_exists(conn, schema, table) if conn is not None else None
        msg = "would COPY"
        if exists is False:
            msg = "table missing in database"
        return TableResult(
            table=table,
            status="dry_run",
            csv_rows=csv_rows,
            db_rows=None,
            duration_sec=round(time.perf_counter() - t0, 3),
            message=msg,
        )

    assert conn is not None
    if not table_exists(conn, schema, table):
        conn.rollback()
        return TableResult(
            table=table,
            status="failed",
            csv_rows=csv_rows,
            message=f"table {schema}.{table} does not exist",
        )

    try:
        if truncate_each:
            with conn.cursor() as cur:
                cur.execute(
                    f"TRUNCATE TABLE {qualify(schema, table)} RESTART IDENTITY CASCADE"
                )

        copy_csv_into_table(
            conn,
            schema=schema,
            table=table,
            path=path,
            columns=columns,
            verbose=verbose,
        )
        sync_identity_sequence(conn, schema, table)

        db_rows = count_table_rows(conn, schema, table)
        if db_rows != csv_rows:
            conn.rollback()
            return TableResult(
                table=table,
                status="failed",
                csv_rows=csv_rows,
                db_rows=db_rows,
                duration_sec=round(time.perf_counter() - t0, 3),
                message=f"row count mismatch (csv={csv_rows}, db={db_rows}); rolled back",
            )

        conn.commit()
        return TableResult(
            table=table,
            status="loaded",
            csv_rows=csv_rows,
            db_rows=db_rows,
            duration_sec=round(time.perf_counter() - t0, 3),
            message="ok",
        )
    except Exception as exc:  # noqa: BLE001 — surface to summary / resume
        conn.rollback()
        return TableResult(
            table=table,
            status="failed",
            csv_rows=csv_rows,
            duration_sec=round(time.perf_counter() - t0, 3),
            message=format_copy_error(exc, table=table),
        )


def run_load(args: argparse.Namespace) -> int:
    data_dir = resolve_data_dir(args.data_dir)
    schema = args.schema
    started = datetime.now(timezone.utc).isoformat()
    wall0 = time.perf_counter()

    extras = discover_extra_csvs(data_dir)
    if extras and args.verbose:
        print(f"[warn] CSV files not in load order (ignored): {', '.join(extras)}", flush=True)

    state = load_state(data_dir) if args.resume and not args.truncate else {"completed": {}, "version": 1}
    if args.truncate:
        clear_state(data_dir)
        state = {"completed": {}, "version": 1}

    summary = LoadSummary(
        started_at=started,
        data_dir=str(data_dir),
        schema=schema,
    )

    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not args.dry_run and not database_url:
        raise SystemExit("DATABASE_URL environment variable is required (unless --dry-run)")

    conn = None
    if not args.dry_run:
        conn = connect(database_url)
        if args.verbose:
            print(f"[connect] {normalize_psycopg_url(database_url).split('@')[-1]}", flush=True)
        if args.truncate:
            # Truncate all known tables once up front (children via CASCADE).
            try:
                truncate_tables(conn, schema, TRUNCATE_ORDER, verbose=args.verbose)
            except Exception as exc:  # noqa: BLE001
                conn.close()
                raise SystemExit(f"Truncate failed: {exc}") from exc

    planned: list[tuple[str, Path | None]] = []
    for table in LOAD_ORDER:
        path = csv_path_for(data_dir, table)
        planned.append((table, path if path.exists() else None))

    bar = ProgressBar(len(planned), desc="Loading", enabled=not args.quiet)
    stop_on_fail = not args.continue_on_error

    try:
        for table, path in planned:
            completed = state.get("completed", {})
            if (
                args.resume
                and not args.truncate
                and not args.dry_run
                and table in completed
                and completed[table].get("status") == "loaded"
            ):
                result = TableResult(
                    table=table,
                    status="skipped_resume",
                    csv_rows=completed[table].get("csv_rows"),
                    db_rows=completed[table].get("db_rows"),
                    message="already loaded (resume)",
                )
                summary.results.append(result)
                summary.tables_skipped += 1
                if args.verbose:
                    print(f"[skip] {table} (resume)", flush=True)
                bar.update(1)
                continue

            if path is None:
                result = TableResult(
                    table=table,
                    status="skipped_missing",
                    message=f"missing file {table}.csv",
                )
                summary.results.append(result)
                summary.tables_missing += 1
                summary.tables_skipped += 1
                print(f"[missing] {table}.csv", flush=True)
                bar.update(1)
                if args.fail_on_missing:
                    summary.tables_failed += 1
                    result.status = "failed"
                    break
                continue

            if args.verbose or args.dry_run:
                print(f"[table] {table}", flush=True)

            result = load_one_table(
                conn,
                schema=schema,
                table=table,
                path=path,
                truncate_each=False,  # full truncate handled up front when --truncate
                dry_run=args.dry_run,
                verbose=args.verbose,
            )
            summary.results.append(result)

            if result.status == "loaded":
                summary.tables_loaded += 1
                summary.rows_loaded += int(result.csv_rows or 0)
                state.setdefault("completed", {})[table] = {
                    "status": "loaded",
                    "csv_rows": result.csv_rows,
                    "db_rows": result.db_rows,
                    "loaded_at": datetime.now(timezone.utc).isoformat(),
                }
                if not args.dry_run:
                    save_state(data_dir, state)
                print(
                    f"[ok] {table}: {result.csv_rows:,} rows in {result.duration_sec}s",
                    flush=True,
                )
            elif result.status == "dry_run":
                summary.tables_loaded += 1  # planned
                summary.rows_loaded += int(result.csv_rows or 0)
                print(f"[dry-run] {table}: {result.csv_rows:,} rows - {result.message}", flush=True)
            elif result.status == "failed":
                summary.tables_failed += 1
                print(f"[FAIL] {table}: {result.message}", flush=True)
                bar.update(1)
                if stop_on_fail:
                    break
                continue
            else:
                summary.tables_skipped += 1

            bar.update(1)
    finally:
        bar.close()
        if conn is not None:
            conn.close()

    summary.finished_at = datetime.now(timezone.utc).isoformat()
    summary.duration_sec = round(time.perf_counter() - wall0, 3)
    print_summary(summary)
    return 1 if summary.tables_failed else 0


def print_summary(summary: LoadSummary) -> None:
    print("", flush=True)
    print("=" * 72, flush=True)
    print("OLTP LOAD SUMMARY", flush=True)
    print("=" * 72, flush=True)
    print(f"Data dir        : {summary.data_dir}", flush=True)
    print(f"Schema          : {summary.schema}", flush=True)
    print(f"Tables loaded   : {summary.tables_loaded}", flush=True)
    print(f"Rows loaded     : {summary.rows_loaded:,}", flush=True)
    print(f"Skipped         : {summary.tables_skipped}", flush=True)
    print(f"Missing files   : {summary.tables_missing}", flush=True)
    print(f"Failures        : {summary.tables_failed}", flush=True)
    print(f"Duration        : {summary.duration_sec:.3f}s", flush=True)
    print("-" * 72, flush=True)
    for r in summary.results:
        csv_r = f"{r.csv_rows:,}" if r.csv_rows is not None else "-"
        db_r = f"{r.db_rows:,}" if r.db_rows is not None else "-"
        dur = f"{r.duration_sec:.3f}s" if r.duration_sec is not None else "-"
        match = ""
        if r.csv_rows is not None and r.db_rows is not None:
            match = " OK" if r.csv_rows == r.db_rows else " MISMATCH"
        print(
            f"  {r.table:<28} {r.status:<16} csv={csv_r:<10} db={db_r:<10} {dur}{match}",
            flush=True,
        )
        if r.message and r.status == "failed":
            for line in r.message.splitlines():
                print(f"    -> {line}", flush=True)
    print("=" * 72, flush=True)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Load data/generated/*.csv into PostgreSQL oltp schema via COPY",
    )
    p.add_argument(
        "--data-dir",
        default=None,
        help=f"Directory containing CSV extracts (default: {DEFAULT_DATA_DIR})",
    )
    p.add_argument(
        "--schema",
        default=DEFAULT_SCHEMA,
        help="Target schema (default: oltp)",
    )
    p.add_argument(
        "--truncate",
        action="store_true",
        help="TRUNCATE all target tables (CASCADE) before load; clears resume state",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan load and count CSV rows without writing to the database",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose logging",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Disable progress bar",
    )
    p.add_argument(
        "--no-resume",
        dest="resume",
        action="store_false",
        help="Ignore _load_state.json and reload all present CSVs",
    )
    p.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Abort if any ordered CSV file is missing",
    )
    p.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue loading remaining tables after a failure",
    )
    p.set_defaults(resume=True)
    return p


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        return run_load(args)
    except KeyboardInterrupt:
        print("\nInterrupted.", flush=True)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
