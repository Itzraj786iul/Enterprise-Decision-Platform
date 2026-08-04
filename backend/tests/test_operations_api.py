"""Unit tests for Operations Intelligence endpoints (mocked analytics services)."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.analytics.services.operations import OperationsAnalyticsService
from app.analytics.services.sales import SalesAnalyticsService
from app.api.routes.operations import get_operations_service
from app.main import create_app
from app.services.operations import OperationsService


@pytest.fixture()
def operations_client():
    operations = MagicMock(spec=OperationsAnalyticsService)
    sales = MagicMock(spec=SalesAnalyticsService)

    today = date(2024, 6, 30)
    operations.get_inventory_rows.return_value = [
        {
            "product_id": 1,
            "sku": "SKU-1",
            "product_name": "Widget A",
            "category_name": "Electronics",
            "store_id": 10,
            "store_name": "Store West",
            "dc_id": 1,
            "dc_name": "DC West",
            "quantity_on_hand": 100,
            "reorder_point": 20,
            "inventory_value_cost": 5000,
            "stock_status": "Healthy",
        },
        {
            "product_id": 2,
            "sku": "SKU-2",
            "product_name": "Widget B",
            "category_name": "Home",
            "store_id": 11,
            "store_name": "Store East",
            "dc_id": 2,
            "dc_name": "DC East",
            "quantity_on_hand": 0,
            "reorder_point": 15,
            "inventory_value_cost": 0,
            "stock_status": "Stockout",
        },
        {
            "product_id": 3,
            "sku": "SKU-3",
            "product_name": "Widget C",
            "category_name": "Electronics",
            "store_id": 10,
            "dc_name": "DC West",
            "quantity_on_hand": 8,
            "reorder_point": 10,
            "inventory_value_cost": 400,
            "stock_status": "Below Reorder",
        },
    ]
    operations.get_supplier_rows.return_value = [
        {
            "supplier_id": 1,
            "supplier_name": "Acme Supply",
            "on_time_rate": 0.92,
            "reliability_score": 0.88,
            "avg_actual_lead_time_days": 5,
            "units_ordered": 1000,
        },
        {
            "supplier_id": 2,
            "supplier_name": "Late Co",
            "on_time_rate": 0.45,
            "reliability_score": 0.5,
            "avg_actual_lead_time_days": 12,
            "units_ordered": 400,
        },
    ]
    operations.get_return_rows.return_value = [
        {
            "return_date": today - timedelta(days=i),
            "product_id": 1 if i % 2 == 0 else 2,
            "quantity_returned": 2,
            "refund_line_amount": 50 + i,
        }
        for i in range(15)
    ] + [
        {
            "return_date": today - timedelta(days=40 + i),
            "product_id": 1,
            "quantity_returned": 1,
            "refund_line_amount": 20,
        }
        for i in range(5)
    ]
    operations.get_shipment_rows.return_value = [
        {
            "dc_name": "DC West",
            "order_date": today - timedelta(days=i),
            "delay_flag": "On Track" if i % 3 else "Delayed Ship",
            "shipment_status": "Delivered",
            "fulfillment_lead_time_days": 2 + (i % 3),
        }
        for i in range(12)
    ]

    sales.get_sales_summary_rows.return_value = [
        {
            "order_date": today - timedelta(days=i),
            "store_id": 10 if i % 2 == 0 else 11,
            "region_name": "West" if i % 2 == 0 else "East",
            "region_code": "W" if i % 2 == 0 else "E",
            "units_sold": 50,
        }
        for i in range(30)
    ]
    sales.get_product_category_rows.return_value = [
        {"product_id": 1, "category_name": "Electronics"},
        {"product_id": 2, "category_name": "Home"},
    ]

    service = OperationsService(operations, sales)
    app = create_app()
    app.dependency_overrides[get_operations_service] = lambda: service
    with TestClient(app) as client:
        yield client, service
    app.dependency_overrides.clear()


def test_operations_overview(operations_client) -> None:
    client, _ = operations_client
    response = client.get("/api/v1/operations/overview")
    assert response.status_code == 200
    ids = {m["id"] for m in response.json()["metrics"]}
    assert ids == {
        "inventory_value",
        "inventory_health",
        "stock_turnover",
        "supplier_performance",
        "return_rate",
        "fulfillment_rate",
    }
    value = next(m for m in response.json()["metrics"] if m["id"] == "inventory_value")
    assert value["available"] is True


def test_operations_overview_unavailable(operations_client) -> None:
    client, service = operations_client
    service.operations.get_inventory_rows.return_value = []
    service.operations.get_supplier_rows.return_value = []
    service.operations.get_return_rows.return_value = []
    service.operations.get_shipment_rows.return_value = []
    service.sales.get_sales_summary_rows.return_value = []
    response = client.get("/api/v1/operations/overview")
    assert response.status_code == 200
    for metric in response.json()["metrics"]:
        assert metric["available"] is False


def test_inventory_pagination_sort_search(operations_client) -> None:
    client, _ = operations_client
    response = client.get(
        "/api/v1/operations/inventory?page=1&page_size=1&sort_by=inventory_value&search=Widget"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert body["pagination"]["page_size"] == 1
    assert len(body["rows"]) == 1
    row = body["rows"][0]
    assert {"product", "category", "stock", "safety_stock", "turnover", "inventory_value"} <= set(row)


def test_supplier_performance(operations_client) -> None:
    client, _ = operations_client
    response = client.get("/api/v1/operations/supplier-performance")
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert any(r["supplier"] == "Acme Supply" for r in rows)
    assert all("risk_level" in r for r in rows)


def test_returns(operations_client) -> None:
    client, _ = operations_client
    response = client.get("/api/v1/operations/returns")
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert any(r["category"] == "Electronics" for r in body["rows"])


def test_warehouse_performance(operations_client) -> None:
    client, _ = operations_client
    response = client.get("/api/v1/operations/warehouse-performance")
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert any(r["warehouse"] == "DC West" for r in rows)


def test_operational_risks(operations_client) -> None:
    client, _ = operations_client
    response = client.get("/api/v1/operations/operational-risks")
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert len(body["rows"]) >= 1
    assert {"risk", "severity", "owner", "recommendation"} <= set(body["rows"][0])
