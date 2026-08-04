"""Operations Intelligence API response schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import PaginationMeta, ResponseMeta, utc_now


class OperationsMetric(BaseModel):
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


class OperationsOverviewResponse(BaseModel):
    metrics: list[OperationsMetric]
    period_start: date | None = None
    period_end: date | None = None
    generated_at: datetime = Field(default_factory=utc_now)
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class InventoryRow(BaseModel):
    product: str
    product_id: str | None = None
    sku: str | None = None
    category: str | None = None
    stock: float | None = None
    safety_stock: float | None = None
    turnover: float | None = None
    inventory_value: float | None = None
    stock_status: str | None = None


class InventoryResponse(BaseModel):
    rows: list[InventoryRow]
    pagination: PaginationMeta
    available: bool = True
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class SupplierPerformanceRow(BaseModel):
    supplier: str
    supplier_id: str | None = None
    on_time_pct: float | None = None
    quality_score: float | None = None
    lead_time: float | None = None
    purchase_volume: float | None = None
    risk_level: str | None = None


class SupplierPerformanceResponse(BaseModel):
    rows: list[SupplierPerformanceRow]
    available: bool = True
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class ReturnsRow(BaseModel):
    category: str
    return_count: float | None = None
    return_pct: float | None = None
    return_cost: float | None = None
    trend: Literal["up", "down", "flat"] | None = None


class ReturnsResponse(BaseModel):
    rows: list[ReturnsRow]
    available: bool = True
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class WarehousePerformanceRow(BaseModel):
    warehouse: str
    inventory: float | None = None
    fulfillment: float | None = None
    stockouts: float | None = None
    average_processing_time: float | None = None


class WarehousePerformanceResponse(BaseModel):
    rows: list[WarehousePerformanceRow]
    available: bool = True
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class OperationalRiskRow(BaseModel):
    risk: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    owner: str | None = None
    recommendation: str | None = None


class OperationalRisksResponse(BaseModel):
    rows: list[OperationalRiskRow]
    available: bool = True
    meta: ResponseMeta = Field(default_factory=ResponseMeta)
