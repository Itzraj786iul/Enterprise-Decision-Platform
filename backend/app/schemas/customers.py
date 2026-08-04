"""Customer Intelligence API response schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.common import PaginationMeta, ResponseMeta, utc_now


class CustomerMetric(BaseModel):
    id: str
    label: str
    value: float | int | None = None
    formatted_value: str | None = None
    unit: str | None = None
    delta: float | None = None
    delta_label: str | None = None
    trend: Literal["up", "down", "flat"] | None = None
    format: Literal["currency", "percent", "number"] | None = None
    available: bool = True
    source: str | None = None


class CustomerOverviewResponse(BaseModel):
    metrics: list[CustomerMetric]
    period_start: date | None = None
    period_end: date | None = None
    generated_at: datetime = Field(default_factory=utc_now)
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class RfmSegmentRow(BaseModel):
    segment: str
    customer_count: float | None = None
    revenue: float | None = None
    average_order_value: float | None = None
    growth: float | None = None


class RfmSegmentsResponse(BaseModel):
    rows: list[RfmSegmentRow]
    available: bool = True
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class CohortRetentionCell(BaseModel):
    month_offset: int
    retention_pct: float | None = None
    customer_count: float | None = None


class CohortRow(BaseModel):
    cohort: str
    cohort_size: float | None = None
    retentions: list[CohortRetentionCell] = Field(default_factory=list)


class CohortsResponse(BaseModel):
    rows: list[CohortRow]
    available: bool = True
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class CustomerDistributionRow(BaseModel):
    region: str
    customer_count: float | None = None
    revenue: float | None = None
    growth: float | None = None


class CustomerDistributionResponse(BaseModel):
    rows: list[CustomerDistributionRow]
    available: bool = True
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class TopCustomerDetailRow(BaseModel):
    customer_id: str | None = None
    customer: str
    segment: str | None = None
    region: str | None = None
    lifetime_value: float | None = None
    orders: float | None = None
    average_order_value: float | None = None
    lifecycle_status: str | None = None
    last_order_date: date | str | None = None


class TopCustomersDetailResponse(BaseModel):
    rows: list[TopCustomerDetailRow]
    pagination: PaginationMeta
    available: bool = True
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class ChurnRiskRow(BaseModel):
    risk_level: str
    customer_count: float | None = None
    predicted_revenue_at_risk: float | None = None
    confidence: float | None = None
    confidence_available: bool = False


class ChurnRiskResponse(BaseModel):
    rows: list[ChurnRiskRow]
    available: bool = True
    source: str | None = "machine_learning_predictions"
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class CustomerInsightItem(BaseModel):
    id: str
    title: str
    body: str
    tone: Literal["info", "success", "warning", "danger"] = "info"
    raw: dict[str, Any] = Field(default_factory=dict)
