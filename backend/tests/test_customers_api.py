"""Unit tests for Customer Intelligence endpoints (mocked analytics services)."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.analytics.services.customer import CustomerAnalyticsService
from app.analytics.services.ml import MachineLearningService
from app.analytics.services.sales import SalesAnalyticsService
from app.api.routes.customers import get_customer_service
from app.main import create_app
from app.schemas.analytics import AnalyticsTablePage, TableColumn, TableResult
from app.schemas.common import PaginationMeta
from app.services.customers import CustomerService


def _table(rows: list[dict]) -> AnalyticsTablePage:
    columns = [TableColumn(key=k, label=k) for k in (rows[0].keys() if rows else [])]
    return AnalyticsTablePage(
        table=TableResult(columns=columns, rows=rows),
        pagination=PaginationMeta(page=1, page_size=100, total_items=len(rows), total_pages=1),
    )


@pytest.fixture()
def customers_client():
    customers = MagicMock(spec=CustomerAnalyticsService)
    sales = MagicMock(spec=SalesAnalyticsService)
    ml = MagicMock(spec=MachineLearningService)

    today = date(2024, 6, 30)
    customer_rows = [
        {
            "customer_id": 1,
            "customer_number": "C-1",
            "preferred_store_id": 10,
            "is_active": True,
            "lifecycle_status": "Active",
            "order_count": 5,
            "lifetime_net_sales": 4000,
            "avg_order_value": 800,
            "first_order_date": today - timedelta(days=120),
            "last_order_date": today - timedelta(days=5),
            "registration_date": today - timedelta(days=130),
        },
        {
            "customer_id": 2,
            "customer_number": "C-2",
            "preferred_store_id": 11,
            "is_active": True,
            "lifecycle_status": "At Risk",
            "order_count": 2,
            "lifetime_net_sales": 900,
            "avg_order_value": 450,
            "first_order_date": today - timedelta(days=10),
            "last_order_date": today - timedelta(days=10),
            "registration_date": today - timedelta(days=10),
        },
        {
            "customer_id": 3,
            "customer_number": "C-3",
            "preferred_store_id": 10,
            "is_active": False,
            "lifecycle_status": "Churn Risk",
            "order_count": 3,
            "lifetime_net_sales": 1500,
            "avg_order_value": 500,
            "first_order_date": today - timedelta(days=200),
            "last_order_date": today - timedelta(days=100),
            "registration_date": today - timedelta(days=210),
        },
    ]
    customers.get_customer_360_rows.return_value = customer_rows
    customers.get_customer_rfm_rows.return_value = [
        {
            "customer_id": 1,
            "rfm_segment": "Champions",
            "lifetime_net_sales": 4000,
            "order_count": 5,
            "last_order_date": today - timedelta(days=5),
        },
        {
            "customer_id": 2,
            "rfm_segment": "Promising New",
            "lifetime_net_sales": 900,
            "order_count": 2,
            "last_order_date": today - timedelta(days=10),
        },
        {
            "customer_id": 3,
            "rfm_segment": "At Risk Loyal",
            "lifetime_net_sales": 1500,
            "order_count": 3,
            "last_order_date": today - timedelta(days=100),
        },
    ]

    sales.get_sales_summary_rows.return_value = [
        {"store_id": 10, "region_name": "West", "region_code": "W", "order_date": today},
        {"store_id": 11, "region_name": "East", "region_code": "E", "order_date": today},
    ]

    ml.get_predictions.return_value = _table(
        [
            {
                "model_name": "churn_model",
                "entity_id": "1",
                "customer_id": 1,
                "score": 0.82,
                "confidence": 0.9,
                "label": "churn",
            },
            {
                "model_name": "churn_model",
                "entity_id": "2",
                "customer_id": 2,
                "score": 0.45,
                "confidence": 0.7,
                "label": "churn",
            },
            {
                "model_name": "churn_model",
                "entity_id": "3",
                "customer_id": 3,
                "score": 0.2,
                "confidence": 0.6,
                "label": "retain",
            },
        ]
    )

    service = CustomerService(customers, sales, ml)
    app = create_app()
    app.dependency_overrides[get_customer_service] = lambda: service
    with TestClient(app) as client:
        yield client, service
    app.dependency_overrides.clear()


def test_customers_overview(customers_client) -> None:
    client, _ = customers_client
    response = client.get("/api/v1/customers/overview")
    assert response.status_code == 200
    ids = {m["id"] for m in response.json()["metrics"]}
    assert ids == {
        "active_customers",
        "new_customers",
        "repeat_customers",
        "avg_ltv",
        "retention_rate",
        "churn_risk_summary",
    }
    active = next(m for m in response.json()["metrics"] if m["id"] == "active_customers")
    assert active["available"] is True
    assert active["value"] is not None


def test_customers_overview_unavailable(customers_client) -> None:
    client, service = customers_client
    service.customers.get_customer_360_rows.return_value = []
    response = client.get("/api/v1/customers/overview")
    assert response.status_code == 200
    for metric in response.json()["metrics"]:
        assert metric["available"] is False


def test_rfm_segments(customers_client) -> None:
    client, _ = customers_client
    response = client.get("/api/v1/customers/rfm-segments")
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert any(r["segment"] == "Champions" for r in body["rows"])
    row = body["rows"][0]
    assert {"segment", "customer_count", "revenue", "average_order_value", "growth"} <= set(row)


def test_cohorts(customers_client) -> None:
    client, _ = customers_client
    response = client.get("/api/v1/customers/cohorts")
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert len(body["rows"]) >= 1
    assert body["rows"][0]["retentions"]
    assert body["rows"][0]["retentions"][0]["month_offset"] == 0


def test_customer_distribution(customers_client) -> None:
    client, _ = customers_client
    response = client.get("/api/v1/customers/customer-distribution")
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert any(r["region"] == "West" for r in rows)


def test_top_customers_sort_page_search(customers_client) -> None:
    client, _ = customers_client
    response = client.get(
        "/api/v1/customers/top-customers?page=1&page_size=1&sort_by=lifetime_value&search=C-1"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["page_size"] == 1
    assert len(body["rows"]) == 1
    assert "C-1" in body["rows"][0]["customer"]


def test_churn_risk(customers_client) -> None:
    client, _ = customers_client
    response = client.get("/api/v1/customers/churn-risk")
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    levels = {r["risk_level"] for r in body["rows"]}
    assert "High" in levels
    high = next(r for r in body["rows"] if r["risk_level"] == "High")
    assert high["confidence_available"] is True
