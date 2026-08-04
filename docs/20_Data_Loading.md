# 20 — OLTP Data Loading (Neon / PostgreSQL)

Automated bulk load of synthetic CSVs into the `oltp` schema using **PostgreSQL COPY** via **psycopg3**.

Related: [19 Neon Deployment](./19_Neon_Deployment.md) · [data_generation README](../data_generation/README.md)

---

## Architecture

```text
data/generated/<table>.csv
        │
        ▼
scripts/load_database.py
        │  psycopg3 COPY ... FROM STDIN (CSV HEADER)
        ▼
oltp.<table>   (FK-safe order, per-table transaction + row validation)
        │
        ▼
_load_state.json  (resume checkpoint)
```

| Concern | Design |
|---------|--------|
| Transport | `COPY ... FROM STDIN WITH (FORMAT csv, HEADER true, NULL '')` |
| Normalization | Stream rows in memory: integer `1.0`→`1`; `NaN`/`None`/`<NA>`/blank→NULL. **CSVs on disk unchanged** |
| Order | Hard-coded FK-safe list matching `database/schema.sql` |
| Transactions | One transaction **per table**; commit only after CSV vs DB row-count match |
| Failure | Rollback that table; report table/column/line/value when COPY provides context |
| Sequences | `setval` on identity/serial PK after each successful COPY |
| Analytics / API / frontend | **Not touched** |

This loader does **not** run `analytical_views.sql` or load ML prediction CSVs. For ML staging use `sql/load_ml_predictions.sql` after analytics views exist.

---

## Prerequisites

1. Schema applied:

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/schema.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/indexes.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/views.sql
```

2. CSVs available (demo or full):

```bash
# Prefer writing into the EDP repo path
python -m data_generation.generate_all --demo
# → enterprise-decision-platform/data/generated/*.csv
```

Or point at an existing directory (e.g. parent workspace demo output).

3. Dependencies:

```bash
python -m pip install "psycopg[binary]"
```

(`backend/requirements.txt` already pins `psycopg[binary]==3.2.6`.)

4. Environment — use Neon **direct** (non-pooled) host for bulk load when possible:

```bash
# PowerShell
$env:DATABASE_URL = "postgresql://USER:PASSWORD@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require"

# bash
export DATABASE_URL="postgresql://USER:PASSWORD@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require"
```

The loader rewrites `postgresql+psycopg://` → `postgresql://` and sets `sslmode=require` for `*.neon.tech` if omitted.

---

## Execution

From **enterprise-decision-platform** repository root:

### Default (auto-detect `data/generated/`)

```bash
python scripts/load_database.py
```

### Explicit data directory (common when CSVs live outside the repo)

```bash
python scripts/load_database.py \
  --data-dir "E:/Conulsting project/data/generated"
```

### Fresh reload (wipe then load)

```bash
python scripts/load_database.py \
  --data-dir "E:/Conulsting project/data/generated" \
  --truncate
```

`--truncate` issues `TRUNCATE ... RESTART IDENTITY CASCADE` across the load-order tables and clears `_load_state.json`.

### Dry run (no writes)

```bash
python scripts/load_database.py \
  --data-dir "E:/Conulsting project/data/generated" \
  --dry-run \
  --verbose
```

`DATABASE_URL` is **not** required for `--dry-run`.

### Verbose

```bash
python scripts/load_database.py --data-dir "..." --verbose
```

---

## CLI reference

| Flag | Meaning |
|------|---------|
| `--data-dir PATH` | CSV directory (default: `data/generated/`) |
| `--schema NAME` | Target schema (default: `oltp`) |
| `--truncate` | Truncate all target tables before load; reset resume state |
| `--dry-run` | Count/plan only |
| `--verbose` | Extra logging |
| `--quiet` | Hide progress bar |
| `--no-resume` | Ignore checkpoint; attempt all CSVs again |
| `--fail-on-missing` | Abort if any ordered CSV is absent |
| `--continue-on-error` | Keep going after a table failure |

---

## Resume

Checkpoint file: `<data-dir>/_load_state.json`

After each successful table (validated row counts), the loader records:

```json
{
  "version": 1,
  "completed": {
    "orders": {
      "status": "loaded",
      "csv_rows": 15000,
      "db_rows": 15000,
      "loaded_at": "..."
    }
  }
}
```

On the next run (default `--resume` behavior):

- Tables marked `loaded` are **skipped**
- Remaining tables continue in FK order

Disable resume:

```bash
python scripts/load_database.py --data-dir "..." --no-resume --truncate
```

Use `--truncate` when reloading into a partially filled database to avoid primary-key conflicts.

---

## Validation

After every `COPY`:

1. `SELECT COUNT(*)` on the target table  
2. Compare to CSV data-row count (header excluded)  
3. On mismatch → **ROLLBACK** that table; status `failed`  
4. On match → sync identity sequence → **COMMIT** → update resume state  

Summary printed at end:

- Tables loaded / skipped / missing / failures  
- Total rows loaded  
- Wall-clock duration  
- Per-table csv vs db counts  

---

## Recommended Neon sequence

```bash
cd "E:/Conulsting project/enterprise-decision-platform"

$env:DATABASE_URL = "postgresql://USER:PASSWORD@DIRECT_HOST/DB?sslmode=require"

# 1) DDL (if not already applied)
psql $env:DATABASE_URL -v ON_ERROR_STOP=1 -f database/schema.sql
psql $env:DATABASE_URL -v ON_ERROR_STOP=1 -f database/indexes.sql
psql $env:DATABASE_URL -v ON_ERROR_STOP=1 -f database/views.sql

# 2) Load OLTP
python scripts/load_database.py `
  --data-dir "E:/Conulsting project/data/generated" `
  --truncate `
  --verbose

# 3) Analytics views (safe before or after load; empty until data exists)
psql $env:DATABASE_URL -v ON_ERROR_STOP=1 -f sql/analytical_views.sql
# If ML/DQ views still missing:
psql $env:DATABASE_URL -v ON_ERROR_STOP=1 -f sql/patches/001_neon_ml_dq_views.sql

# 4) Optional ML staging
psql $env:DATABASE_URL -v ON_ERROR_STOP=1 -f sql/load_ml_predictions.sql

# 5) Spot checks
psql $env:DATABASE_URL -c "SELECT COUNT(*) FROM oltp.orders;"
psql $env:DATABASE_URL -c "SELECT COUNT(*) FROM analytics.vw_sales_daily;"
```

---

## Load order (FK-safe)

`calendar_date` → `regions` → `channels` → `payment_methods` → `distribution_centers` → `stores` → `product_categories` → `suppliers` → `customers` → `loyalty_accounts` → `customer_addresses` → `products` → `product_suppliers` → `price_history` / `cost_history` → `employees` → `promotions` → `marketing_campaigns` → `orders` → `order_items` → `order_item_promotions` → `payments` → `shipments` → `shipment_items` → `returns` → `return_items` → `campaign_responses` → `inventory` → `inventory_transactions` → `inventory_snapshots` → `purchase_orders` → `purchase_order_items` → `goods_receipts` → `goods_receipt_items` → `store_labor_hours`

Unknown `*.csv` files in the data directory are ignored (listed under `--verbose`).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `DATABASE_URL is required` | Env not set | Export/set `DATABASE_URL` |
| SSL / connection errors to Neon | Pooled host or missing SSL | Use **direct** endpoint; `sslmode=require` |
| `duplicate key` on resume | Reloading without truncate | `--truncate` or truncate conflicting tables |
| `foreign key` violation | Wrong order / incomplete parents | Ensure full CSV set; do not reorder `LOAD_ORDER` casually |
| Row count mismatch | Truncated mid-file / concurrent writers | Fix source CSV; re-run with `--truncate` |
| Missing files | Demo dir incomplete | Re-run `generate_all` or remove `--fail-on-missing` |
| `psycopg` import error | Dep missing | `pip install 'psycopg[binary]'` |
| Slow over network | Large `inventory_snapshots` | Expected; keep session alive; use resume after failure |

---

## Out of scope

- Analytics view creation / ML prediction load  
- API or frontend changes  
- Regenerating synthetic data  
- Manual `\copy` workflows (replaced by this script)
