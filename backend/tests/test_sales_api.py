"""Unit tests for Sales Intelligence endpoints (mocked analytics services)."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.analytics.services.customer import CustomerAnalyticsService
from app.analytics.services.sales import SalesAnalyticsService
from app.api.routes.sales import get_sales_service
from app.main import create_app
from app.schemas.analytics import AnalyticsTablePage, TableColumn, TableResult
from app.schemas.common import PaginationMeta
from app.services.sales import SalesService


def _table(rows: list[dict]) -> AnalyticsTablePage:
    columns = [TableColumn(key=k, label=k) for k in (rows[0].keys() if rows else [])]
    return AnalyticsTablePage(
        table=TableResult(columns=columns, rows=rows),
        pagination=PaginationMeta(page=1, page_size=100, total_items=len(rows), total_pages=1),
    )


@pytest.fixture()
def sales_client():
    sales = MagicMock(spec=SalesAnalyticsService)
    customers = MagicMock(spec=CustomerAnalyticsService)

    today = date(2024, 6, 30)
    summary = []
    for i in range(60):
        d = today - timedelta(days=59 - i)
        summary.append(
            {
                "order_date": d,
                "region_name": "West" if i % 2 == 0 else "East",
                "channel_name": "Retail",
                "net_sales": 1000 + i * 10,
                "gross_profit": 300 + i * 2,
                "order_count": 20 + i,
            }
        )
    sales.get_sales_summary_rows.return_value = summary

    lines = []
    for i in range(20):
        d = today - timedelta(days=i)
        lines.append(
            {
                "order_date": d,
                "order_id": 100 + i,
                "product_id": 1 if i % 2 == 0 else 2,
                "line_net_amount": 200 + i,
                "line_gross_profit": 60 + i,
                "quantity": 2,
            }
        )
        # prior window
        lines.append(
            {
                "order_date": today - timedelta(days=40 + i),
                "order_id": 200 + i,
                "product_id": 1 if i % 2 == 0 else 2,
                "line_net_amount": 150 + i,
                "line_gross_profit": 40 + i,
                "quantity": 1,
            }
        )
    sales.get_sales_line_rows.return_value = lines
    sales.get_product_category_rows.return_value = [
        {
            "product_id": 1,
            "sku": "SKU-1",
            "product_name": "Alpha Widget",
            "category_name": "Electronics",
        },
        {
            "product_id": 2,
            "sku": "SKU-2",
            "product_name": "Beta Gadget",
            "category_name": "Home",
        },
    ]

    customers.get_customer_360.return_value = _table(
        [
            {
                "customer_id": 10,
                "customer_number": "C-10",
                "order_count": 12,
                "lifetime_net_sales": 5000,
            },
            {
                "customer_id": 11,
                "customer_number": "C-11",
                "order_count": 8,
                "lifetime_net_sales": 3200,
            },
        ]
    )

    service = SalesService(sales, customers)
    app = create_app()
    app.dependency_overrides[get_sales_service] = lambda: service
    with TestClient(app) as client:
        yield client, service
    app.dependency_overrides.clear()


def test_sales_overview_endpoint(sales_client) -> None:
    client, _ = sales_client
    response = client.get("/api/v1/sales/overview")
    assert response.status_code == 200
    body = response.json()
    ids = {m["id"] for m in body["metrics"]}
    assert ids == {"revenue", "orders", "aov", "gross_profit", "profit_margin", "growth"}
    revenue = next(m for m in body["metrics"] if m["id"] == "revenue")
    assert revenue["available"] is True
    assert revenue["value"] is not None


def test_sales_overview_unavailable_when_empty(sales_client) -> None:
    client, service = sales_client
    service.sales.get_sales_summary_rows.return_value = []
    response = client.get("/api/v1/sales/overview")
    assert response.status_code == 200
    for metric in response.json()["metrics"]:
        if metric["id"] in {"revenue", "orders", "gross_profit"}:
            assert metric["available"] is False


def test_sales_trends_grains(sales_client) -> None:
    client, _ = sales_client
    for grain in ("daily", "weekly", "monthly"):
        response = client.get(f"/api/v1/sales/trends?grain={grain}")
        assert response.status_code == 200
        body = response.json()
        assert body["grain"] == grain
        assert body["available"] is True
        assert len(body["points"]) > 0
        assert "revenue" in body["points"][0]
        assert "orders" in body["points"][0]
        assert "profit" in body["points"][0]


def test_category_performance_endpoint(sales_client) -> None:
    client, _ = sales_client
    response = client.get("/api/v1/sales/category-performance")
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert any(r["category"] == "Electronics" for r in body["rows"])
    row = body["rows"][0]
    assert "revenue" in row and "orders" in row and "growth" in row and "margin" in row


def test_product_performance_sorting_pagination_search(sales_client) -> None:
    client, _ = sales_client
    response = client.get(
        "/api/v1/sales/product-performance?page=1&page_size=1&sort_by=revenue&sort_dir=desc&search=Alpha"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert body["pagination"]["page_size"] == 1
    assert len(body["rows"]) == 1
    assert "Alpha" in body["rows"][0]["product"]


def test_regional_performance_endpoint(sales_client) -> None:
    client, _ = sales_client
    response = client.get("/api/v1/sales/regional-performance")
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert any(r["region"] == "West" for r in rows)


def test_top_customers_endpoint(sales_client) -> None:
    client, _ = sales_client
    response = client.get("/api/v1/sales/top-customers?limit=2")
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert len(body["rows"]) == 2
    assert body["rows"][0]["lifetime_value_available"] is True
