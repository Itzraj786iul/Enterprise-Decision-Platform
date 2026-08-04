"""Customer Intelligence API routes."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Request

from app.analytics.services.customer import CustomerAnalyticsService
from app.analytics.services.ml import MachineLearningService
from app.analytics.services.sales import SalesAnalyticsService
from app.api.dependencies.analytics import (
    get_customer_analytics_service,
    get_ml_analytics_service,
    get_sales_analytics_service,
)
from app.schemas.common import ResponseMeta
from app.schemas.customers import (
    ChurnRiskResponse,
    CohortsResponse,
    CustomerDistributionResponse,
    CustomerOverviewResponse,
    RfmSegmentsResponse,
    TopCustomersDetailResponse,
)
from app.services.customers import CustomerService

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


def get_customer_service(
    customers: Annotated[CustomerAnalyticsService, Depends(get_customer_analytics_service)],
    sales: Annotated[SalesAnalyticsService, Depends(get_sales_analytics_service)],
    machine_learning: Annotated[MachineLearningService, Depends(get_ml_analytics_service)],
) -> CustomerService:
    return CustomerService(customers, sales, machine_learning)


CustomerSvc = Annotated[CustomerService, Depends(get_customer_service)]


def _with_request_meta(request: Request, response_model):
    meta = ResponseMeta(request_id=getattr(request.state, "request_id", None))
    return response_model.model_copy(update={"meta": meta})


def _split_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    parts = [part.strip() for part in value.split(",") if part.strip()]
    return parts or None


@router.get("/overview", response_model=CustomerOverviewResponse)
def customers_overview(
    request: Request,
    service: CustomerSvc,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    region: str | None = Query(default=None),
    segment: str | None = Query(default=None, description="Comma-separated RFM segments"),
    search: str | None = Query(default=None, max_length=200),
) -> CustomerOverviewResponse:
    return _with_request_meta(
        request,
        service.get_overview(
            date_from=date_from,
            date_to=date_to,
            region=_split_csv(region),
            segment=_split_csv(segment),
            search=search,
        ),
    )


@router.get("/rfm-segments", response_model=RfmSegmentsResponse)
def customers_rfm_segments(
    request: Request,
    service: CustomerSvc,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    segment: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
) -> RfmSegmentsResponse:
    return _with_request_meta(
        request,
        service.get_rfm_segments(
            date_from=date_from,
            date_to=date_to,
            segment=_split_csv(segment),
            search=search,
        ),
    )


@router.get("/cohorts", response_model=CohortsResponse)
def customers_cohorts(
    request: Request,
    service: CustomerSvc,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    region: str | None = Query(default=None),
    segment: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
) -> CohortsResponse:
    return _with_request_meta(
        request,
        service.get_cohorts(
            date_from=date_from,
            date_to=date_to,
            region=_split_csv(region),
            segment=_split_csv(segment),
            search=search,
        ),
    )


@router.get("/customer-distribution", response_model=CustomerDistributionResponse)
def customers_distribution(
    request: Request,
    service: CustomerSvc,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    region: str | None = Query(default=None),
    segment: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
) -> CustomerDistributionResponse:
    return _with_request_meta(
        request,
        service.get_customer_distribution(
            date_from=date_from,
            date_to=date_to,
            region=_split_csv(region),
            segment=_split_csv(segment),
            search=search,
        ),
    )


@router.get("/top-customers", response_model=TopCustomersDetailResponse)
def customers_top(
    request: Request,
    service: CustomerSvc,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="lifetime_value"),
    sort_dir: Literal["asc", "desc"] = Query(default="desc"),
    search: str | None = Query(default=None, max_length=200),
    columns: str | None = Query(default=None),
    region: str | None = Query(default=None),
    segment: str | None = Query(default=None),
) -> TopCustomersDetailResponse:
    return _with_request_meta(
        request,
        service.get_top_customers(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
            search=search,
            columns=_split_csv(columns),
            region=_split_csv(region),
            segment=_split_csv(segment),
        ),
    )


@router.get("/churn-risk", response_model=ChurnRiskResponse)
def customers_churn_risk(
    request: Request,
    service: CustomerSvc,
    search: str | None = Query(default=None, max_length=200),
    segment: str | None = Query(default=None),
) -> ChurnRiskResponse:
    return _with_request_meta(
        request,
        service.get_churn_risk(search=search, segment=_split_csv(segment)),
    )
