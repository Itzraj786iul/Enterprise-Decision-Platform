"""Sales Intelligence API response schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.common import PaginationMeta, ResponseMeta, utc_now


class SalesMetric(BaseModel):
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


class SalesOverviewResponse(BaseModel):
    metrics: list[SalesMetric]
    period_start: date | None = None
    period_end: date | None = None
    generated_at: datetime = Field(default_factory=utc_now)
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class SalesTrendPoint(BaseModel):
    period: str
    revenue: float | None = None
    orders: float | None = None
    profit: float | None = None


class SalesTrendsResponse(BaseModel):
    points: list[SalesTrendPoint]
    grain: Literal["daily", "weekly", "monthly"]
    available: bool = True
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class CategoryPerformanceRow(BaseModel):
    category: str
    revenue: float | None = None
    orders: float | None = None
    growth: float | None = None
    margin: float | None = None


class CategoryPerformanceResponse(BaseModel):
    rows: list[CategoryPerformanceRow]
    available: bool = True
    source: str | None = "fact_sales_line+product_category_map"
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class ProductPerformanceRow(BaseModel):
    product_id: str | None = None
    product: str
    sku: str | None = None
    category: str | None = None
    revenue: float | None = None
    orders: float | None = None
    units: float | None = None
    margin: float | None = None
    growth: float | None = None


class ProductPerformanceResponse(BaseModel):
    rows: list[ProductPerformanceRow]
    pagination: PaginationMeta
    available: bool = True
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class RegionalSalesRow(BaseModel):
    region: str
    revenue: float | None = None
    orders: float | None = None
    growth: float | None = None


class RegionalSalesResponse(BaseModel):
    rows: list[RegionalSalesRow]
    available: bool = True
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class TopCustomerRow(BaseModel):
    customer: str
    customer_id: str | None = None
    revenue: float | None = None
    orders: float | None = None
    lifetime_value: float | None = None
    lifetime_value_available: bool = False


class TopCustomersResponse(BaseModel):
    rows: list[TopCustomerRow]
    available: bool = True
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class SalesInsightItem(BaseModel):
    id: str
    title: str
    body: str
    tone: Literal["info", "success", "warning", "danger"] = "info"


class SalesRecommendationItem(BaseModel):
    id: str
    title: str
    summary: str
    priority: Literal["low", "medium", "high"] = "medium"
    raw: dict[str, Any] = Field(default_factory=dict)
