"""Unit tests for executive dashboard endpoints (mocked analytics services)."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.analytics.services.data_quality import DataQualityService
from app.analytics.services.executive import ExecutiveAnalyticsService
from app.analytics.services.ml import MachineLearningService
from app.api.routes.dashboard import get_dashboard_service
from app.main import create_app
from app.schemas.analytics import AnalyticsTablePage, TableColumn, TableResult
from app.schemas.common import PaginationMeta
from app.services.dashboard import DashboardService


def _table(rows: list[dict]) -> AnalyticsTablePage:
    columns = [TableColumn(key=k, label=k) for k in (rows[0].keys() if rows else [])]
    return AnalyticsTablePage(
        table=TableResult(columns=columns, rows=rows),
        pagination=PaginationMeta(page=1, page_size=100, total_items=len(rows), total_pages=1),
    )


@pytest.fixture()
def dashboard_client():
    executive = MagicMock(spec=ExecutiveAnalyticsService)
    data_quality = MagicMock(spec=DataQualityService)
    ml = MagicMock(spec=MachineLearningService)

    today = date(2024, 6, 30)
    scorecard = []
    for i in range(60):
        d = today - timedelta(days=59 - i)
        scorecard.append(
            {
                "order_date": d,
                "net_sales": 1000 + i * 10,
                "gross_profit": 300 + i * 2,
                "margin_pct": 0.3,
                "order_count": 20 + i,
                "stockout_positions": 5,
                "snapshot_positions": 100,
            }
        )
    executive.get_scorecard_rows.return_value = scorecard
    executive.get_commercial_detail.return_value = _table(
        [
            {
                "order_date": today,
                "region_name": "West",
                "net_sales": 5000,
                "gross_profit": 1500,
                "order_count": 40,
            },
            {
                "order_date": today - timedelta(days=40),
                "region_name": "West",
                "net_sales": 4000,
                "gross_profit": 1200,
                "order_count": 35,
            },
            {
                "order_date": today,
                "region_name": "East",
                "net_sales": 3000,
                "gross_profit": 900,
                "order_count": 25,
            },
        ]
    )
    data_quality.get_quality_summary.return_value = _table(
        [{"check_name": "completeness", "score": 0.92, "severity": "info"}]
    )
    ml.get_predictions.return_value = _table(
        [
            {
                "model_name": "churn_model",
                "entity_type": "customer",
                "entity_id": "C1",
                "score": 0.81,
                "label": "churn",
            },
            {
                "model_name": "uplift_model",
                "entity_type": "customer",
                "entity_id": "C2",
                "score": 0.77,
                "label": "opportunity",
                "title": "Cross-sell opportunity",
            },
        ]
    )

    service = DashboardService(executive, data_quality, ml)
    app = create_app()
    app.dependency_overrides[get_dashboard_service] = lambda: service
    with TestClient(app) as client:
        yield client, service
    app.dependency_overrides.clear()


def test_overview_endpoint(dashboard_client) -> None:
    client, _ = dashboard_client
    response = client.get("/api/v1/dashboard/overview?days=30")
    assert response.status_code == 200
    body = response.json()
    ids = {m["id"] for m in body["metrics"]}
    assert ids == {
        "revenue",
        "profit",
        "profit_margin",
        "revenue_growth",
        "active_customers",
        "inventory_health",
        "dq_score",
        "overall_churn_risk",
    }
    revenue = next(m for m in body["metrics"] if m["id"] == "revenue")
    assert revenue["available"] is True
    assert revenue["value"] is not None


def test_trends_endpoint(dashboard_client) -> None:
    client, _ = dashboard_client
    response = client.get("/api/v1/dashboard/trends?days=30")
    assert response.status_code == 200
    body = response.json()
    assert len(body["points"]) == 30
    assert body["points"][0]["revenue"] is not None


def test_regional_performance_endpoint(dashboard_client) -> None:
    client, _ = dashboard_client
    response = client.get("/api/v1/dashboard/regional-performance?days=30")
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert any(r["region"] == "West" for r in rows)


def test_top_risks_endpoint(dashboard_client) -> None:
    client, _ = dashboard_client
    response = client.get("/api/v1/dashboard/top-risks")
    assert response.status_code == 200
    items = response.json()["items"]
    assert any(i["source"] == "machine_learning_predictions" for i in items)


def test_opportunities_endpoint(dashboard_client) -> None:
    client, _ = dashboard_client
    response = client.get("/api/v1/dashboard/opportunities")
    assert response.status_code == 200
    items = response.json()["items"]
    assert any("opportunity" in i["title"].lower() or i["source"] == "machine_learning_predictions" for i in items)
