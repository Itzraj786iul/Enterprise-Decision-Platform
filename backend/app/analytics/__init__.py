"""Analytics read-only access layer."""

from app.analytics.caching import AnalyticsCache, NullCache, build_cache_key
from app.analytics.config import AnalyticsViewKey, AnalyticsViewRegistry, default_view_catalog
from app.analytics.query import (
    AnalyticsQuery,
    FilterClause,
    FilterOperator,
    validate_query_against_view,
)
from app.analytics.repositories import AnalyticsRepositoryFactory, AnalyticsViewRepository
from app.analytics.services import (
    CustomerAnalyticsService,
    DataQualityService,
    ExecutiveAnalyticsService,
    FinanceAnalyticsService,
    MachineLearningService,
    OperationsAnalyticsService,
    RecommendationService,
    SalesAnalyticsService,
)

__all__ = [
    "AnalyticsCache",
    "AnalyticsQuery",
    "AnalyticsRepositoryFactory",
    "AnalyticsViewKey",
    "AnalyticsViewRegistry",
    "AnalyticsViewRepository",
    "CustomerAnalyticsService",
    "DataQualityService",
    "ExecutiveAnalyticsService",
    "FilterClause",
    "FilterOperator",
    "FinanceAnalyticsService",
    "MachineLearningService",
    "NullCache",
    "OperationsAnalyticsService",
    "RecommendationService",
    "SalesAnalyticsService",
    "build_cache_key",
    "default_view_catalog",
    "validate_query_against_view",
]
