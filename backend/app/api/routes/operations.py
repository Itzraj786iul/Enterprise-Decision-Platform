"""Operations Intelligence API routes."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Request

from app.analytics.services.operations import OperationsAnalyticsService
from app.analytics.services.sales import SalesAnalyticsService
from app.api.dependencies.analytics import (
    get_operations_analytics_service,
    get_sales_analytics_service,
)
from app.schemas.common import ResponseMeta
from app.schemas.operations import (
    InventoryResponse,
    OperationalRisksResponse,
    OperationsOverviewResponse,
    ReturnsResponse,
    SupplierPerformanceResponse,
    WarehousePerformanceResponse,
)
from app.services.operations import OperationsService

router = APIRouter(prefix="/api/v1/operations", tags=["operations"])


def get_operations_service(
    operations: Annotated[OperationsAnalyticsService, Depends(get_operations_analytics_service)],
    sales: Annotated[SalesAnalyticsService, Depends(get_sales_analytics_service)],
) -> OperationsService:
    return OperationsService(operations, sales)


OperationsSvc = Annotated[OperationsService, Depends(get_operations_service)]


def _with_request_meta(request: Request, response_model):
    meta = ResponseMeta(request_id=getattr(request.state, "request_id", None))
    return response_model.model_copy(update={"meta": meta})


def _split_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    parts = [part.strip() for part in value.split(",") if part.strip()]
    return parts or None


@router.get("/overview", response_model=OperationsOverviewResponse)
def operations_overview(
    request: Request,
    service: OperationsSvc,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    region: str | None = Query(default=None),
    category: str | None = Query(default=None),
    supplier: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
) -> OperationsOverviewResponse:
    return _with_request_meta(
        request,
        service.get_overview(
            date_from=date_from,
            date_to=date_to,
            region=_split_csv(region),
            category=_split_csv(category),
            supplier=_split_csv(supplier),
            search=search,
        ),
    )


@router.get("/inventory", response_model=InventoryResponse)
def operations_inventory(
    request: Request,
    service: OperationsSvc,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="inventory_value"),
    sort_dir: Literal["asc", "desc"] = Query(default="desc"),
    search: str | None = Query(default=None, max_length=200),
    columns: str | None = Query(default=None),
    category: str | None = Query(default=None),
    region: str | None = Query(default=None),
) -> InventoryResponse:
    return _with_request_meta(
        request,
        service.get_inventory(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
            search=search,
            columns=_split_csv(columns),
            category=_split_csv(category),
            region=_split_csv(region),
        ),
    )


@router.get("/supplier-performance", response_model=SupplierPerformanceResponse)
def operations_supplier_performance(
    request: Request,
    service: OperationsSvc,
    supplier: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
) -> SupplierPerformanceResponse:
    return _with_request_meta(
        request,
        service.get_supplier_performance(
            supplier=_split_csv(supplier),
            search=search,
        ),
    )


@router.get("/returns", response_model=ReturnsResponse)
def operations_returns(
    request: Request,
    service: OperationsSvc,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    category: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
) -> ReturnsResponse:
    return _with_request_meta(
        request,
        service.get_returns(
            date_from=date_from,
            date_to=date_to,
            category=_split_csv(category),
            search=search,
        ),
    )


@router.get("/warehouse-performance", response_model=WarehousePerformanceResponse)
def operations_warehouse_performance(
    request: Request,
    service: OperationsSvc,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    region: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
) -> WarehousePerformanceResponse:
    return _with_request_meta(
        request,
        service.get_warehouse_performance(
            date_from=date_from,
            date_to=date_to,
            region=_split_csv(region),
            search=search,
        ),
    )


@router.get("/operational-risks", response_model=OperationalRisksResponse)
def operations_risks(
    request: Request,
    service: OperationsSvc,
    category: str | None = Query(default=None),
    supplier: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
) -> OperationalRisksResponse:
    return _with_request_meta(
        request,
        service.get_operational_risks(
            category=_split_csv(category),
            supplier=_split_csv(supplier),
            search=search,
        ),
    )
