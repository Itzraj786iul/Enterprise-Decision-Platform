"""Pydantic DTOs for analytics read responses."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from app.schemas.common import PaginationMeta, ResponseMeta, utc_now

T = TypeVar("T")


class AnalyticsFilterSchema(BaseModel):
    column: str
    op: str = "eq"
    value: Any | None = None


class AnalyticsQueryParams(BaseModel):
    """API/service input mirror of AnalyticsQuery."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=500)
    sort_by: str | None = None
    sort_dir: str = "desc"
    date_from: date | None = None
    date_to: date | None = None
    date_column: str | None = None
    search: str | None = None
    filters: list[AnalyticsFilterSchema] = Field(default_factory=list)
    columns: list[str] | None = None


class KpiCard(BaseModel):
    id: str
    title: str
    value: float | int | str | None = None
    unit: str | None = None
    delta: float | None = None
    delta_label: str | None = None
    trend: str | None = None  # up | down | flat
    format: str | None = None  # currency | percent | number
    meta: dict[str, Any] = Field(default_factory=dict)


class SummaryMetrics(BaseModel):
    metrics: dict[str, float | int | str | None] = Field(default_factory=dict)
    as_of: date | datetime | None = None
    notes: str | None = None


class TrendPoint(BaseModel):
    x: date | datetime | str
    y: float | int | None = None
    label: str | None = None
    dimensions: dict[str, Any] = Field(default_factory=dict)


class TrendSeries(BaseModel):
    id: str
    name: str
    unit: str | None = None
    points: list[TrendPoint] = Field(default_factory=list)


class TimeSeriesResponse(BaseModel):
    series: list[TrendSeries]
    grain: str | None = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class TableColumn(BaseModel):
    key: str
    label: str
    type: str | None = None


class TableResult(BaseModel):
    columns: list[TableColumn] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)


class AnalyticsPage(BaseModel, Generic[T]):
    items: list[T]
    pagination: PaginationMeta
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class AnalyticsTablePage(BaseModel):
    table: TableResult
    pagination: PaginationMeta
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class KpiDashboardBundle(BaseModel):
    """DTO bundle for future dashboard routers — not an API route."""

    kpis: list[KpiCard] = Field(default_factory=list)
    summary: SummaryMetrics | None = None
    trends: list[TrendSeries] = Field(default_factory=list)
    table: TableResult | None = None
    generated_at: datetime = Field(default_factory=utc_now)
