"""Analytics service orchestration tests (mocked repositories — no SQL)."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.analytics.caching import NullCache, build_cache_key
from app.analytics.config import AnalyticsViewKey, AnalyticsViewRegistry
from app.analytics.query import AnalyticsQuery
from app.analytics.repositories.factory import AnalyticsRepositoryFactory
from app.analytics.services.recommendations import UnimplementedRecommendationService
from app.analytics.services.sales import SalesAnalyticsService


@pytest.fixture()
def sales_service() -> SalesAnalyticsService:
    registry = AnalyticsViewRegistry()
    session = MagicMock()
    factory = AnalyticsRepositoryFactory(session, registry=registry)
    service = SalesAnalyticsService(factory, cache=NullCache())

    repo = MagicMock()
    repo.fetch_page.return_value = (
        [
            {
                "order_date": date(2024, 1, 1),
                "net_sales": 100.0,
                "gross_sales": 120.0,
                "gross_profit": 40.0,
                "order_count": 2,
                "units_sold": 5,
            }
        ],
        1,
    )
    repo.summarize_numeric.return_value = {
        "net_sales": 100.0,
        "gross_sales": 120.0,
        "gross_profit": 40.0,
        "order_count": 2.0,
        "units_sold": 5.0,
    }
    service.factory.for_view = MagicMock(return_value=repo)  # type: ignore[method-assign]
    service._test_repo = repo  # type: ignore[attr-defined]
    return service


def test_sales_summary_returns_paginated_table(sales_service: SalesAnalyticsService) -> None:
    page = sales_service.get_sales_summary(AnalyticsQuery(page=1, page_size=10))
    assert page.pagination.total_items == 1
    assert page.table.rows[0]["net_sales"] == 100.0
    sales_service._test_repo.fetch_page.assert_called_once()  # type: ignore[attr-defined]


def test_sales_kpi_cards_compose_summary(sales_service: SalesAnalyticsService) -> None:
    cards = sales_service.get_sales_kpi_cards()
    assert len(cards) == 4
    assert cards[0].id == "net_sales"
    assert cards[0].value == 100.0


def test_sales_time_series_dto(sales_service: SalesAnalyticsService) -> None:
    series = sales_service.get_net_sales_time_series()
    assert series.grain == "day"
    assert series.series[0].points[0].y == 100.0


def test_recommendation_service_interface_only() -> None:
    service = UnimplementedRecommendationService()
    with pytest.raises(NotImplementedError):
        service.list_recommendations()


def test_cache_key_stable() -> None:
    a = build_cache_key("sales", {"page": 1})
    b = build_cache_key("sales", {"page": 1})
    c = build_cache_key("sales", {"page": 2})
    assert a == b
    assert a != c


def test_service_uses_logical_view_key(sales_service: SalesAnalyticsService) -> None:
    sales_service.get_sales_summary()
    sales_service.factory.for_view.assert_called_with(AnalyticsViewKey.SALES_SUMMARY)
