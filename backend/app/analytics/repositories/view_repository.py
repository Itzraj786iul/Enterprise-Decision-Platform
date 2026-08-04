"""Read-only SQLAlchemy repository for analytics views."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Any

from sqlalchemy import MetaData, Table, asc, desc, func, or_, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session
from sqlalchemy.sql import ColumnElement

from app.analytics.config import AnalyticsViewDefinition
from app.analytics.query import AnalyticsQuery, FilterClause, FilterOperator
from app.core.exceptions import DatabaseError, ValidationAppError
from app.core.logging import get_logger

logger = get_logger("app.analytics.repository")


class AnalyticsViewRepository:
    """
    Generic read-only access to a single analytics SQL view.
    Never writes. Never targets OLTP tables.
    """

    def __init__(self, session: Session, view: AnalyticsViewDefinition) -> None:
        self.session = session
        self.view = view
        self._table: Table | None = None

    @property
    def table(self) -> Table:
        if self._table is None:
            metadata = MetaData()
            try:
                self._table = Table(
                    self.view.name,
                    metadata,
                    schema=self.view.schema,
                    autoload_with=self.session.get_bind(),
                )
            except Exception as exc:  # noqa: BLE001
                raise DatabaseError(
                    f"Unable to load analytics view '{self.view.qualified_name}'",
                    details={"error": str(exc)},
                ) from exc
        return self._table

    def _column(self, name: str) -> ColumnElement[Any]:
        if name not in self.table.c:
            raise ValidationAppError(
                f"Unknown column '{name}' on view '{self.view.key.value}'",
                details={"available": list(self.table.c.keys())},
            )
        return self.table.c[name]

    def _apply_filters(self, clauses: Sequence[FilterClause]) -> list[ColumnElement[Any]]:
        predicates: list[ColumnElement[Any]] = []
        for clause in clauses:
            col = self._column(clause.column)
            op = clause.op
            if op == FilterOperator.EQ:
                predicates.append(col == clause.value)
            elif op == FilterOperator.NE:
                predicates.append(col != clause.value)
            elif op == FilterOperator.GT:
                predicates.append(col > clause.value)
            elif op == FilterOperator.GTE:
                predicates.append(col >= clause.value)
            elif op == FilterOperator.LT:
                predicates.append(col < clause.value)
            elif op == FilterOperator.LTE:
                predicates.append(col <= clause.value)
            elif op == FilterOperator.IN:
                predicates.append(col.in_(list(clause.value)))
            elif op == FilterOperator.LIKE:
                predicates.append(col.like(str(clause.value)))
            elif op == FilterOperator.ILIKE:
                predicates.append(col.ilike(str(clause.value)))
            elif op == FilterOperator.IS_NULL:
                predicates.append(col.is_(None))
            elif op == FilterOperator.IS_NOT_NULL:
                predicates.append(col.is_not(None))
            else:
                raise ValidationAppError(f"Unsupported filter operator: {op}")
        return predicates

    def _where_clauses(self, query: AnalyticsQuery) -> list[ColumnElement[Any]]:
        predicates = self._apply_filters(query.filters)
        if query.date_from or query.date_to:
            if query.date_column is None:
                raise ValidationAppError("date_column is required for date range filters")
            date_col = self._column(query.date_column)
            if query.date_from is not None:
                predicates.append(date_col >= query.date_from)
            if query.date_to is not None:
                predicates.append(date_col <= query.date_to)
        if query.search and self.view.searchable_columns:
            pattern = f"%{query.search}%"
            search_preds = [
                self._column(col).ilike(pattern)
                for col in self.view.searchable_columns
                if col in self.table.c
            ]
            if search_preds:
                predicates.append(or_(*search_preds))
        return predicates

    def _select_columns(self, query: AnalyticsQuery) -> list[ColumnElement[Any]]:
        if query.columns:
            return [self._column(name) for name in query.columns]
        if self.view.allowed_columns:
            cols = [self._column(name) for name in self.view.allowed_columns if name in self.table.c]
            return cols or list(self.table.c)
        return list(self.table.c)

    def _apply_sort(self, stmt, query: AnalyticsQuery):  # type: ignore[no-untyped-def]
        if not query.sort_by:
            return stmt
        col = self._column(query.sort_by)
        return stmt.order_by(asc(col) if query.sort_dir == "asc" else desc(col))

    def count(self, query: AnalyticsQuery) -> int:
        where = self._where_clauses(query)
        stmt = select(func.count()).select_from(self.table)
        if where:
            stmt = stmt.where(*where)
        try:
            return int(self.session.scalar(stmt) or 0)
        except Exception as exc:  # noqa: BLE001
            raise DatabaseError(
                "Failed to count analytics view rows",
                details={"view": self.view.qualified_name, "error": str(exc)},
            ) from exc

    def fetch(self, query: AnalyticsQuery) -> list[dict[str, Any]]:
        where = self._where_clauses(query)
        cols = self._select_columns(query)
        stmt = select(*cols).select_from(self.table)
        if where:
            stmt = stmt.where(*where)
        stmt = self._apply_sort(stmt, query)
        stmt = stmt.offset(query.offset).limit(query.limit)
        try:
            rows = self.session.execute(stmt).mappings().all()
            return [dict(row) for row in rows]
        except Exception as exc:  # noqa: BLE001
            raise DatabaseError(
                "Failed to fetch analytics view rows",
                details={"view": self.view.qualified_name, "error": str(exc)},
            ) from exc

    def fetch_page(self, query: AnalyticsQuery) -> tuple[list[dict[str, Any]], int]:
        total = self.count(query)
        items = self.fetch(query) if total else []
        return items, total

    def stream(
        self,
        query: AnalyticsQuery,
        *,
        yield_per: int = 500,
        max_rows: int | None = 10_000,
    ) -> Iterator[dict[str, Any]]:
        """Stream large result sets without full materialization."""
        where = self._where_clauses(query)
        cols = self._select_columns(query)
        stmt = select(*cols).select_from(self.table)
        if where:
            stmt = stmt.where(*where)
        stmt = self._apply_sort(stmt, query)
        if max_rows is not None:
            stmt = stmt.limit(max_rows)
        try:
            result = self.session.execute(stmt).yield_per(yield_per)
            for row in result.mappings():
                mapping: RowMapping = row
                yield dict(mapping)
        except Exception as exc:  # noqa: BLE001
            raise DatabaseError(
                "Failed to stream analytics view rows",
                details={"view": self.view.qualified_name, "error": str(exc)},
            ) from exc

    def summarize_numeric(
        self,
        query: AnalyticsQuery,
        columns: Sequence[str],
    ) -> dict[str, float | None]:
        """Aggregate SUM for selected numeric columns (read-only)."""
        where = self._where_clauses(query)
        aggregates = [func.sum(self._column(name)).label(name) for name in columns]
        stmt = select(*aggregates).select_from(self.table)
        if where:
            stmt = stmt.where(*where)
        try:
            row = self.session.execute(stmt).mappings().first()
            if not row:
                return {name: None for name in columns}
            return {
                name: (float(row[name]) if row[name] is not None else None) for name in columns
            }
        except Exception as exc:  # noqa: BLE001
            raise DatabaseError(
                "Failed to summarize analytics view",
                details={"view": self.view.qualified_name, "error": str(exc)},
            ) from exc
