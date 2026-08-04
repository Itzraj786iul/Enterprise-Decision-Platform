"""Finance Intelligence API response schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ResponseMeta, utc_now


class FinanceMetric(BaseModel):
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


class FinanceOverviewResponse(BaseModel):
    metrics: list[FinanceMetric]
    period_start: date | None = None
    period_end: date | None = None
    generated_at: datetime = Field(default_factory=utc_now)
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class ProfitabilityRow(BaseModel):
    region: str
    revenue: float | None = None
    cost: float | None = None
    profit: float | None = None
    margin: float | None = None
    growth: float | None = None


class ProfitabilityResponse(BaseModel):
    rows: list[ProfitabilityRow]
    available: bool = True
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class CostBreakdownRow(BaseModel):
    cost_category: str
    amount: float | None = None
    percentage: float | None = None
    trend: Literal["up", "down", "flat"] | None = None


class CostBreakdownResponse(BaseModel):
    rows: list[CostBreakdownRow]
    available: bool = True
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class CashflowRow(BaseModel):
    period: str
    inflows: float | None = None
    outflows: float | None = None
    net_cashflow: float | None = None
    profit: float | None = None
    margin: float | None = None


class CashflowResponse(BaseModel):
    rows: list[CashflowRow]
    available: bool = True
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class FinancialRiskRow(BaseModel):
    risk: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    estimated_impact: float | None = None
    owner: str | None = None
    recommendation: str | None = None


class FinancialRisksResponse(BaseModel):
    rows: list[FinancialRiskRow]
    available: bool = True
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class BudgetVarianceRow(BaseModel):
    department: str
    budget: float | None = None
    actual: float | None = None
    variance: float | None = None
    variance_pct: float | None = None


class BudgetVarianceResponse(BaseModel):
    rows: list[BudgetVarianceRow]
    available: bool = True
    source: str | None = "campaign_performance"
    meta: ResponseMeta = Field(default_factory=ResponseMeta)
