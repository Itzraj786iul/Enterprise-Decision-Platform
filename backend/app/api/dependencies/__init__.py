"""API dependencies package."""

from app.api.dependencies.analytics import (
    CustomerAnalytics,
    DataQualityAnalytics,
    ExecutiveAnalytics,
    FinanceAnalytics,
    MlAnalytics,
    OperationsAnalytics,
    SalesAnalytics,
    get_analytics_repository_factory,
    get_customer_analytics_service,
    get_sales_analytics_service,
)
from app.api.dependencies.common import (
    AppSettings,
    AuthenticatedUser,
    CurrentUser,
    DbSession,
    RequestLogger,
    get_app_settings,
    get_current_user,
    get_current_user_optional,
    get_request_logger,
)

__all__ = [
    "AppSettings",
    "AuthenticatedUser",
    "CurrentUser",
    "CustomerAnalytics",
    "DataQualityAnalytics",
    "DbSession",
    "ExecutiveAnalytics",
    "FinanceAnalytics",
    "MlAnalytics",
    "OperationsAnalytics",
    "RequestLogger",
    "SalesAnalytics",
    "get_analytics_repository_factory",
    "get_app_settings",
    "get_current_user",
    "get_current_user_optional",
    "get_customer_analytics_service",
    "get_request_logger",
    "get_sales_analytics_service",
]
