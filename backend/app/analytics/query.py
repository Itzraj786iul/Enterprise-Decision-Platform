"""Analytics query specifications and input validation (no SQL)."""

from __future__ import annotations

import math
import re
from datetime import date
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.analytics.config import AnalyticsViewDefinition
from app.core.exceptions import ValidationAppError

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class FilterOperator(str, Enum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    LIKE = "like"
    ILIKE = "ilike"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class FilterClause(BaseModel):
    column: str
    op: FilterOperator = FilterOperator.EQ
    value: Any | None = None

    @field_validator("column")
    @classmethod
    def validate_column_name(cls, value: str) -> str:
        if not _IDENTIFIER_RE.match(value):
            raise ValueError(f"Invalid filter column identifier: {value}")
        return value


class AnalyticsQuery(BaseModel):
    """Transport-agnostic read query for analytics views."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=500)
    sort_by: str | None = None
    sort_dir: Literal["asc", "desc"] = "desc"
    date_from: date | None = None
    date_to: date | None = None
    date_column: str | None = None
    search: str | None = Field(default=None, max_length=200)
    filters: list[FilterClause] = Field(default_factory=list)
    columns: list[str] | None = None
    """Optional column projection. None = all allowed columns."""

    @field_validator("sort_by")
    @classmethod
    def validate_sort_identifier(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _IDENTIFIER_RE.match(value):
            raise ValueError(f"Invalid sort column identifier: {value}")
        return value

    @field_validator("date_column")
    @classmethod
    def validate_date_column_identifier(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _IDENTIFIER_RE.match(value):
            raise ValueError(f"Invalid date column identifier: {value}")
        return value

    @field_validator("columns")
    @classmethod
    def validate_projection(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        if not value:
            raise ValueError("columns projection cannot be an empty list")
        for col in value:
            if not _IDENTIFIER_RE.match(col):
                raise ValueError(f"Invalid projection column identifier: {col}")
        return value

    @model_validator(mode="after")
    def validate_date_range(self) -> AnalyticsQuery:
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be on or before date_to")
        return self

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


def validate_query_against_view(
    query: AnalyticsQuery,
    view: AnalyticsViewDefinition,
    *,
    max_page_size: int = 500,
) -> AnalyticsQuery:
    """Enforce view-specific allowlists for sort/filter/search/projection."""
    if query.page_size > max_page_size:
        raise ValidationAppError(
            f"page_size cannot exceed {max_page_size}",
            details={"page_size": query.page_size, "max": max_page_size},
        )

    allowed = set(view.allowed_columns) if view.allowed_columns else None
    sortable = set(view.sortable_columns) if view.sortable_columns else allowed
    searchable = set(view.searchable_columns) if view.searchable_columns else allowed
    date_cols = set(view.date_columns)

    sort_by = query.sort_by or view.default_sort
    if sort_by and sortable is not None and sort_by not in sortable:
        raise ValidationAppError(
            f"sort_by '{sort_by}' is not allowed for view '{view.key.value}'",
            details={"allowed": sorted(sortable)},
        )

    date_column = query.date_column
    if query.date_from or query.date_to:
        if not date_cols and date_column is None:
            raise ValidationAppError(
                f"View '{view.key.value}' does not support date range filtering",
            )
        date_column = date_column or (view.date_columns[0] if view.date_columns else None)
        if date_column is None or (date_cols and date_column not in date_cols):
            raise ValidationAppError(
                f"date_column '{date_column}' is not allowed",
                details={"allowed": sorted(date_cols)},
            )

    if query.search and searchable is not None and not searchable:
        raise ValidationAppError(f"View '{view.key.value}' does not support search")

    for clause in query.filters:
        if allowed is not None and clause.column not in allowed:
            raise ValidationAppError(
                f"Filter column '{clause.column}' is not allowed",
                details={"allowed": sorted(allowed)},
            )
        if clause.op in {FilterOperator.IN} and not isinstance(clause.value, (list, tuple, set)):
            raise ValidationAppError(
                f"Filter op 'in' requires a list value for column '{clause.column}'",
            )
        if clause.op in {FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL} and clause.value is not None:
            raise ValidationAppError(
                f"Filter op '{clause.op.value}' must not include a value",
            )

    if query.columns and allowed is not None:
        unknown = [c for c in query.columns if c not in allowed]
        if unknown:
            raise ValidationAppError(
                "One or more projection columns are not allowed",
                details={"unknown": unknown, "allowed": sorted(allowed)},
            )

    # Return a copy with normalized defaults
    return query.model_copy(
        update={
            "sort_by": sort_by,
            "date_column": date_column,
        }
    )


def total_pages(total_items: int, page_size: int) -> int:
    if page_size <= 0:
        return 0
    return int(math.ceil(total_items / page_size)) if total_items else 0
