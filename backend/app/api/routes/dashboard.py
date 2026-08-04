"""Executive dashboard API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.analytics.services.data_quality import DataQualityService
from app.analytics.services.executive import ExecutiveAnalyticsService
from app.analytics.services.ml import MachineLearningService
from app.api.dependencies.analytics import (
    get_data_quality_service,
    get_executive_analytics_service,
    get_ml_analytics_service,
)
from app.schemas.common import ResponseMeta
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    DashboardTrendsResponse,
    OpportunitiesResponse,
    RegionalPerformanceResponse,
    TopRisksResponse,
)
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


def get_dashboard_service(
    executive: Annotated[ExecutiveAnalyticsService, Depends(get_executive_analytics_service)],
    data_quality: Annotated[DataQualityService, Depends(get_data_quality_service)],
    machine_learning: Annotated[MachineLearningService, Depends(get_ml_analytics_service)],
) -> DashboardService:
    return DashboardService(executive, data_quality, machine_learning)


DashboardSvc = Annotated[DashboardService, Depends(get_dashboard_service)]


def _with_request_meta(request: Request, response_model):
    meta = ResponseMeta(request_id=getattr(request.state, "request_id", None))
    return response_model.model_copy(update={"meta": meta})


@router.get("/overview", response_model=DashboardOverviewResponse)
def dashboard_overview(
    request: Request,
    service: DashboardSvc,
    days: int = Query(default=30, ge=7, le=365),
) -> DashboardOverviewResponse:
    return _with_request_meta(request, service.get_overview(days=days))


@router.get("/trends", response_model=DashboardTrendsResponse)
def dashboard_trends(
    request: Request,
    service: DashboardSvc,
    days: int = Query(default=90, ge=7, le=365),
) -> DashboardTrendsResponse:
    return _with_request_meta(request, service.get_trends(days=days))


@router.get("/regional-performance", response_model=RegionalPerformanceResponse)
def dashboard_regional_performance(
    request: Request,
    service: DashboardSvc,
    days: int = Query(default=30, ge=7, le=365),
) -> RegionalPerformanceResponse:
    return _with_request_meta(request, service.get_regional_performance(days=days))


@router.get("/top-risks", response_model=TopRisksResponse)
def dashboard_top_risks(
    request: Request,
    service: DashboardSvc,
    limit: int = Query(default=10, ge=1, le=50),
) -> TopRisksResponse:
    return _with_request_meta(request, service.get_top_risks(limit=limit))


@router.get("/opportunities", response_model=OpportunitiesResponse)
def dashboard_opportunities(
    request: Request,
    service: DashboardSvc,
    limit: int = Query(default=10, ge=1, le=50),
) -> OpportunitiesResponse:
    return _with_request_meta(request, service.get_opportunities(limit=limit))
