"""Sales Intelligence API routes."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Request

from app.analytics.services.customer import CustomerAnalyticsService
from app.analytics.services.sales import SalesAnalyticsService
from app.api.dependencies.analytics import (
    get_customer_analytics_service,
    get_sales_analytics_service,
)
from app.schemas.common import ResponseMeta
from app.schemas.sales import (
    CategoryPerformanceResponse,
    ProductPerformanceResponse,
    RegionalSalesResponse,
    SalesOverviewResponse,
    SalesTrendsResponse,
    TopCustomersResponse,
)
from app.services.sales import SalesService

router = APIRouter(prefix="/api/v1/sales", tags=["sales"])


def get_sales_service(
    sales: Annotated[SalesAnalyticsService, Depends(get_sales_analytics_service)],
    customers: Annotated[CustomerAnalyticsService, Depends(get_customer_analytics_service)],
) -> SalesService:
    return SalesService(sales, customers)


SalesSvc = Annotated[SalesService, Depends(get_sales_service)]


def _with_request_meta(request: Request, response_model):
    meta = ResponseMeta(request_id=getattr(request.state, "request_id", None))
    return response_model.model_copy(update={"meta": meta})


def _split_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    parts = [part.strip() for part in value.split(",") if part.strip()]
    return parts or None


@router.get("/overview", response_model=SalesOverviewResponse)
def sales_overview(
    request: Request,
    service: SalesSvc,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    region: str | None = Query(default=None, description="Comma-separated region names"),
    category: str | None = Query(default=None, description="Comma-separated category names"),
    search: str | None = Query(default=None, max_length=200),
) -> SalesOverviewResponse:
    return _with_request_meta(
        request,
        service.get_overview(
            date_from=date_from,
            date_to=date_to,
            region=_split_csv(region),
            category=_split_csv(category),
            search=search,
        ),
    )


@router.get("/trends", response_model=SalesTrendsResponse)
def sales_trends(
    request: Request,
    service: SalesSvc,
    grain: Literal["daily", "weekly", "monthly"] = Query(default="daily"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    region: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
) -> SalesTrendsResponse:
    return _with_request_meta(
        request,
        service.get_trends(
            grain=grain,
            date_from=date_from,
            date_to=date_to,
            region=_split_csv(region),
            search=search,
        ),
    )


@router.get("/category-performance", response_model=CategoryPerformanceResponse)
def sales_category_performance(
    request: Request,
    service: SalesSvc,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    region: str | None = Query(default=None),
    category: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
) -> CategoryPerformanceResponse:
    return _with_request_meta(
        request,
        service.get_category_performance(
            date_from=date_from,
            date_to=date_to,
            region=_split_csv(region),
            category=_split_csv(category),
            search=search,
        ),
    )


@router.get("/product-performance", response_model=ProductPerformanceResponse)
def sales_product_performance(
    request: Request,
    service: SalesSvc,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="revenue"),
    sort_dir: Literal["asc", "desc"] = Query(default="desc"),
    search: str | None = Query(default=None, max_length=200),
    columns: str | None = Query(default=None, description="Comma-separated projection columns"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    category: str | None = Query(default=None),
) -> ProductPerformanceResponse:
    return _with_request_meta(
        request,
        service.get_product_performance(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
            search=search,
            columns=_split_csv(columns),
            date_from=date_from,
            date_to=date_to,
            category=_split_csv(category),
        ),
    )


@router.get("/regional-performance", response_model=RegionalSalesResponse)
def sales_regional_performance(
    request: Request,
    service: SalesSvc,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    region: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
) -> RegionalSalesResponse:
    return _with_request_meta(
        request,
        service.get_regional_performance(
            date_from=date_from,
            date_to=date_to,
            region=_split_csv(region),
            search=search,
        ),
    )


@router.get("/top-customers", response_model=TopCustomersResponse)
def sales_top_customers(
    request: Request,
    service: SalesSvc,
    limit: int = Query(default=10, ge=1, le=50),
    search: str | None = Query(default=None, max_length=200),
) -> TopCustomersResponse:
    return _with_request_meta(
        request,
        service.get_top_customers(limit=limit, search=search),
    )
