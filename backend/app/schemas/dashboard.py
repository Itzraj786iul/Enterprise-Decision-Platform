"""Executive dashboard response schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.common import ResponseMeta, utc_now


class DashboardMetric(BaseModel):
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


class DashboardOverviewResponse(BaseModel):
    metrics: list[DashboardMetric]
    period_start: date | None = None
    period_end: date | None = None
    generated_at: datetime = Field(default_factory=utc_now)
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class DashboardTrendPoint(BaseModel):
    date: date | str
    revenue: float | None = None
    profit: float | None = None
    orders: float | None = None


class DashboardTrendsResponse(BaseModel):
    points: list[DashboardTrendPoint]
    grain: str = "day"
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class RegionalPerformanceRow(BaseModel):
    region: str
    revenue: float | None = None
    profit: float | None = None
    growth: float | None = None
    order_count: float | None = None


class RegionalPerformanceResponse(BaseModel):
    rows: list[RegionalPerformanceRow]
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class RiskItem(BaseModel):
    id: str
    title: str
    description: str | None = None
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    impact: str | None = None
    owner: str | None = None
    source: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class TopRisksResponse(BaseModel):
    items: list[RiskItem]
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class OpportunityItem(BaseModel):
    id: str
    title: str
    description: str | None = None
    estimated_impact: str | None = None
    priority: Literal["low", "medium", "high"] = "medium"
    source: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class OpportunitiesResponse(BaseModel):
    items: list[OpportunityItem]
    meta: ResponseMeta = Field(default_factory=ResponseMeta)
