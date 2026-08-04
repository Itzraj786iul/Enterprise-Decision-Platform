"""Pydantic schemas package."""

from app.schemas.analytics import (
    AnalyticsFilterSchema,
    AnalyticsQueryParams,
    AnalyticsTablePage,
    KpiCard,
    KpiDashboardBundle,
    SummaryMetrics,
    TableColumn,
    TableResult,
    TimeSeriesResponse,
    TrendPoint,
    TrendSeries,
)
from app.schemas.common import (
    BaseResponse,
    ErrorDetail,
    ErrorResponse,
    HealthComponent,
    HealthResponse,
    MessageResponse,
    PaginatedResponse,
    PaginationMeta,
    ResponseMeta,
)

__all__ = [
    "AnalyticsFilterSchema",
    "AnalyticsQueryParams",
    "AnalyticsTablePage",
    "BaseResponse",
    "ErrorDetail",
    "ErrorResponse",
    "HealthComponent",
    "HealthResponse",
    "KpiCard",
    "KpiDashboardBundle",
    "MessageResponse",
    "PaginatedResponse",
    "PaginationMeta",
    "ResponseMeta",
    "SummaryMetrics",
    "TableColumn",
    "TableResult",
    "TimeSeriesResponse",
    "TrendPoint",
    "TrendSeries",
]
