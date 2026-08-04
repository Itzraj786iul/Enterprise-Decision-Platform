"""Analytics dependency injection helpers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.analytics.caching import NullCache
from app.analytics.config import AnalyticsViewRegistry
from app.analytics.repositories.factory import AnalyticsRepositoryFactory
from app.analytics.services.customer import CustomerAnalyticsService
from app.analytics.services.data_quality import DataQualityService
from app.analytics.services.executive import ExecutiveAnalyticsService
from app.analytics.services.finance import FinanceAnalyticsService
from app.analytics.services.ml import MachineLearningService
from app.analytics.services.operations import OperationsAnalyticsService
from app.analytics.services.recommendations import UnimplementedRecommendationService
from app.analytics.services.sales import SalesAnalyticsService
from app.api.dependencies.common import AppSettings, DbSession
from app.core.config import Settings


def get_analytics_registry(settings: AppSettings) -> AnalyticsViewRegistry:
    return AnalyticsViewRegistry(settings=settings)


def get_analytics_repository_factory(
    session: DbSession,
    registry: Annotated[AnalyticsViewRegistry, Depends(get_analytics_registry)],
) -> AnalyticsRepositoryFactory:
    return AnalyticsRepositoryFactory(session, registry=registry)


def get_sales_analytics_service(
    factory: Annotated[AnalyticsRepositoryFactory, Depends(get_analytics_repository_factory)],
    settings: AppSettings,
) -> SalesAnalyticsService:
    return SalesAnalyticsService(
        factory,
        cache=NullCache(),
        cache_ttl_seconds=settings.ANALYTICS_CACHE_TTL_SECONDS,
    )


def get_customer_analytics_service(
    factory: Annotated[AnalyticsRepositoryFactory, Depends(get_analytics_repository_factory)],
    settings: AppSettings,
) -> CustomerAnalyticsService:
    return CustomerAnalyticsService(
        factory,
        cache=NullCache(),
        cache_ttl_seconds=settings.ANALYTICS_CACHE_TTL_SECONDS,
    )


def get_finance_analytics_service(
    factory: Annotated[AnalyticsRepositoryFactory, Depends(get_analytics_repository_factory)],
    settings: AppSettings,
) -> FinanceAnalyticsService:
    return FinanceAnalyticsService(
        factory,
        cache=NullCache(),
        cache_ttl_seconds=settings.ANALYTICS_CACHE_TTL_SECONDS,
    )


def get_operations_analytics_service(
    factory: Annotated[AnalyticsRepositoryFactory, Depends(get_analytics_repository_factory)],
    settings: AppSettings,
) -> OperationsAnalyticsService:
    return OperationsAnalyticsService(
        factory,
        cache=NullCache(),
        cache_ttl_seconds=settings.ANALYTICS_CACHE_TTL_SECONDS,
    )


def get_executive_analytics_service(
    factory: Annotated[AnalyticsRepositoryFactory, Depends(get_analytics_repository_factory)],
    settings: AppSettings,
) -> ExecutiveAnalyticsService:
    return ExecutiveAnalyticsService(
        factory,
        cache=NullCache(),
        cache_ttl_seconds=settings.ANALYTICS_CACHE_TTL_SECONDS,
    )


def get_ml_analytics_service(
    factory: Annotated[AnalyticsRepositoryFactory, Depends(get_analytics_repository_factory)],
    settings: AppSettings,
) -> MachineLearningService:
    return MachineLearningService(
        factory,
        cache=NullCache(),
        cache_ttl_seconds=settings.ANALYTICS_CACHE_TTL_SECONDS,
    )


def get_data_quality_service(
    factory: Annotated[AnalyticsRepositoryFactory, Depends(get_analytics_repository_factory)],
    settings: AppSettings,
) -> DataQualityService:
    return DataQualityService(
        factory,
        cache=NullCache(),
        cache_ttl_seconds=settings.ANALYTICS_CACHE_TTL_SECONDS,
    )


def get_recommendation_service() -> UnimplementedRecommendationService:
    return UnimplementedRecommendationService()


# Annotated aliases for routers (future)
SalesAnalytics = Annotated[SalesAnalyticsService, Depends(get_sales_analytics_service)]
CustomerAnalytics = Annotated[CustomerAnalyticsService, Depends(get_customer_analytics_service)]
FinanceAnalytics = Annotated[FinanceAnalyticsService, Depends(get_finance_analytics_service)]
OperationsAnalytics = Annotated[OperationsAnalyticsService, Depends(get_operations_analytics_service)]
ExecutiveAnalytics = Annotated[ExecutiveAnalyticsService, Depends(get_executive_analytics_service)]
MlAnalytics = Annotated[MachineLearningService, Depends(get_ml_analytics_service)]
DataQualityAnalytics = Annotated[DataQualityService, Depends(get_data_quality_service)]


def build_services_for_session(session, settings: Settings | None = None):  # type: ignore[no-untyped-def]
    """Helper for scripts/tests — not an HTTP dependency."""
    from app.core.config import get_settings

    cfg = settings or get_settings()
    registry = AnalyticsViewRegistry(settings=cfg)
    factory = AnalyticsRepositoryFactory(session, registry=registry)
    cache = NullCache()
    ttl = cfg.ANALYTICS_CACHE_TTL_SECONDS
    return {
        "sales": SalesAnalyticsService(factory, cache=cache, cache_ttl_seconds=ttl),
        "customer": CustomerAnalyticsService(factory, cache=cache, cache_ttl_seconds=ttl),
        "finance": FinanceAnalyticsService(factory, cache=cache, cache_ttl_seconds=ttl),
        "operations": OperationsAnalyticsService(factory, cache=cache, cache_ttl_seconds=ttl),
        "executive": ExecutiveAnalyticsService(factory, cache=cache, cache_ttl_seconds=ttl),
        "ml": MachineLearningService(factory, cache=cache, cache_ttl_seconds=ttl),
        "data_quality": DataQualityService(factory, cache=cache, cache_ttl_seconds=ttl),
        "recommendations": UnimplementedRecommendationService(),
    }
