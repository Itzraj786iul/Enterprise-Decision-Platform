"""Analytics query validation unit tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.analytics.config import AnalyticsViewKey, AnalyticsViewRegistry
from app.analytics.query import (
    AnalyticsQuery,
    FilterClause,
    FilterOperator,
    validate_query_against_view,
)
from app.core.exceptions import ValidationAppError


def test_date_range_order_rejected() -> None:
    with pytest.raises(ValidationError):
        AnalyticsQuery(date_from="2024-05-01", date_to="2024-01-01")


def test_invalid_sort_identifier_rejected() -> None:
    with pytest.raises(ValidationError):
        AnalyticsQuery(sort_by="net_sales;drop table")


def test_validate_query_sort_allowlist() -> None:
    view = AnalyticsViewRegistry().get(AnalyticsViewKey.SALES_SUMMARY)
    with pytest.raises(ValidationAppError):
        validate_query_against_view(
            AnalyticsQuery(sort_by="not_a_real_column"),
            view,
        )


def test_validate_query_normalizes_defaults() -> None:
    view = AnalyticsViewRegistry().get(AnalyticsViewKey.SALES_SUMMARY)
    validated = validate_query_against_view(AnalyticsQuery(), view)
    assert validated.sort_by == "order_date"


def test_validate_date_range_requires_supported_column() -> None:
    view = AnalyticsViewRegistry().get(AnalyticsViewKey.SALES_TRENDS)
    with pytest.raises(ValidationAppError):
        validate_query_against_view(
            AnalyticsQuery(date_from="2024-01-01", date_to="2024-01-31"),
            view,
        )


def test_filter_in_requires_list() -> None:
    view = AnalyticsViewRegistry().get(AnalyticsViewKey.SALES_SUMMARY)
    with pytest.raises(ValidationAppError):
        validate_query_against_view(
            AnalyticsQuery(
                filters=[FilterClause(column="store_code", op=FilterOperator.IN, value="A")],
            ),
            view,
        )


def test_pagination_limits() -> None:
    view = AnalyticsViewRegistry().get(AnalyticsViewKey.CUSTOMER_360)
    with pytest.raises(ValidationAppError):
        validate_query_against_view(AnalyticsQuery(page_size=500), view, max_page_size=100)


def test_projection_allowlist() -> None:
    view = AnalyticsViewRegistry().get(AnalyticsViewKey.SALES_SUMMARY)
    with pytest.raises(ValidationAppError):
        validate_query_against_view(
            AnalyticsQuery(columns=["net_sales", "hacked_column"]),
            view,
        )


def test_view_override_parsing() -> None:
    from app.core.config import Settings

    settings = Settings(
        APP_ENV="testing",
        DATABASE_URL="sqlite:///:memory:",
        JWT_SECRET_KEY="test-secret-key",
        ANALYTICS_VIEW_OVERRIDES="sales_summary=vw_custom_sales",
    )
    registry = AnalyticsViewRegistry(settings=settings)
    definition = registry.get(AnalyticsViewKey.SALES_SUMMARY)
    assert definition.name == "vw_custom_sales"
