"""Finance Intelligence API routes."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.analytics.services.finance import FinanceAnalyticsService
from app.api.dependencies.analytics import get_finance_analytics_service
from app.schemas.common import ResponseMeta
from app.schemas.finance import (
    BudgetVarianceResponse,
    CashflowResponse,
    CostBreakdownResponse,
    FinanceOverviewResponse,
    FinancialRisksResponse,
    ProfitabilityResponse,
)
from app.services.finance import FinanceService

router = APIRouter(prefix="/api/v1/finance", tags=["finance"])


def get_finance_service(
    finance: Annotated[FinanceAnalyticsService, Depends(get_finance_analytics_service)],
) -> FinanceService:
    return FinanceService(finance)


FinanceSvc = Annotated[FinanceService, Depends(get_finance_service)]


def _with_request_meta(request: Request, response_model):
    meta = ResponseMeta(request_id=getattr(request.state, "request_id", None))
    return response_model.model_copy(update={"meta": meta})


def _split_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    parts = [part.strip() for part in value.split(",") if part.strip()]
    return parts or None


@router.get("/overview", response_model=FinanceOverviewResponse)
def finance_overview(
    request: Request,
    service: FinanceSvc,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    region: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
) -> FinanceOverviewResponse:
    return _with_request_meta(
        request,
        service.get_overview(
            date_from=date_from,
            date_to=date_to,
            region=_split_csv(region),
            search=search,
        ),
    )


@router.get("/profitability", response_model=ProfitabilityResponse)
def finance_profitability(
    request: Request,
    service: FinanceSvc,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    region: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
) -> ProfitabilityResponse:
    return _with_request_meta(
        request,
        service.get_profitability(
            date_from=date_from,
            date_to=date_to,
            region=_split_csv(region),
            search=search,
        ),
    )


@router.get("/cost-breakdown", response_model=CostBreakdownResponse)
def finance_cost_breakdown(
    request: Request,
    service: FinanceSvc,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    region: str | None = Query(default=None),
    cost_category: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
) -> CostBreakdownResponse:
    return _with_request_meta(
        request,
        service.get_cost_breakdown(
            date_from=date_from,
            date_to=date_to,
            region=_split_csv(region),
            cost_category=_split_csv(cost_category),
            search=search,
        ),
    )


@router.get("/cashflow", response_model=CashflowResponse)
def finance_cashflow(
    request: Request,
    service: FinanceSvc,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    region: str | None = Query(default=None),
) -> CashflowResponse:
    return _with_request_meta(
        request,
        service.get_cashflow(
            date_from=date_from,
            date_to=date_to,
            region=_split_csv(region),
        ),
    )


@router.get("/financial-risks", response_model=FinancialRisksResponse)
def finance_risks(
    request: Request,
    service: FinanceSvc,
    region: str | None = Query(default=None),
    department: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
) -> FinancialRisksResponse:
    return _with_request_meta(
        request,
        service.get_financial_risks(
            region=_split_csv(region),
            department=_split_csv(department),
            search=search,
        ),
    )


@router.get("/budget-variance", response_model=BudgetVarianceResponse)
def finance_budget_variance(
    request: Request,
    service: FinanceSvc,
    department: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
) -> BudgetVarianceResponse:
    return _with_request_meta(
        request,
        service.get_budget_variance(
            department=_split_csv(department),
            search=search,
        ),
    )
