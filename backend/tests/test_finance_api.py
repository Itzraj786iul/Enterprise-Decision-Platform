"""Unit tests for Finance Intelligence endpoints (mocked analytics services)."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.analytics.services.finance import FinanceAnalyticsService
from app.api.routes.finance import get_finance_service
from app.main import create_app
from app.services.finance import FinanceService


@pytest.fixture()
def finance_client():
    finance = MagicMock(spec=FinanceAnalyticsService)
    today = date(2024, 6, 30)

    finance.get_sales_rows.return_value = [
        {
            "order_date": today - timedelta(days=i),
            "region_name": "West" if i % 2 == 0 else "East",
            "net_sales": 1000 + i * 5,
            "gross_profit": 300 + i,
            "cogs_amount": 600 + i,
            "discount_amount": 50,
        }
        for i in range(60)
    ]
    finance.get_scorecard_rows.return_value = [
        {
            "order_date": today - timedelta(days=i),
            "net_sales": 1000,
            "gross_profit": 300,
            "refund_amount": 40,
            "margin_pct": 0.3,
        }
        for i in range(60)
    ]
    finance.get_payment_rows.return_value = [
        {
            "payment_month": date(2024, m, 1),
            "payment_amount": 20000 + m * 1000,
            "method_name": "Card",
        }
        for m in range(1, 7)
    ]
    finance.get_campaign_rows.return_value = [
        {
            "campaign_type": "Brand",
            "campaign_name": "Spring Brand",
            "budget_amount": 10000,
            "actual_spend": 12000,
        },
        {
            "campaign_type": "Performance",
            "campaign_name": "Search Push",
            "budget_amount": 8000,
            "actual_spend": 7500,
        },
    ]

    service = FinanceService(finance)
    app = create_app()
    app.dependency_overrides[get_finance_service] = lambda: service
    with TestClient(app) as client:
        yield client, service
    app.dependency_overrides.clear()


def test_finance_overview(finance_client) -> None:
    client, _ = finance_client
    response = client.get("/api/v1/finance/overview")
    assert response.status_code == 200
    ids = {m["id"] for m in response.json()["metrics"]}
    assert ids == {
        "revenue",
        "gross_profit",
        "net_profit",
        "profit_margin",
        "operating_cost",
        "cost_ratio",
    }
    revenue = next(m for m in response.json()["metrics"] if m["id"] == "revenue")
    assert revenue["available"] is True


def test_finance_overview_unavailable(finance_client) -> None:
    client, service = finance_client
    service.finance.get_sales_rows.return_value = []
    service.finance.get_scorecard_rows.return_value = []
    response = client.get("/api/v1/finance/overview")
    assert response.status_code == 200
    for metric in response.json()["metrics"]:
        assert metric["available"] is False


def test_profitability(finance_client) -> None:
    client, _ = finance_client
    response = client.get("/api/v1/finance/profitability")
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert any(r["region"] == "West" for r in rows)
    assert {"revenue", "cost", "profit", "margin", "growth"} <= set(rows[0])


def test_cost_breakdown(finance_client) -> None:
    client, _ = finance_client
    response = client.get("/api/v1/finance/cost-breakdown")
    assert response.status_code == 200
    cats = {r["cost_category"] for r in response.json()["rows"]}
    assert "COGS" in cats


def test_cashflow(finance_client) -> None:
    client, _ = finance_client
    response = client.get("/api/v1/finance/cashflow")
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert {"period", "inflows", "outflows", "net_cashflow"} <= set(body["rows"][0])


def test_financial_risks(finance_client) -> None:
    client, _ = finance_client
    response = client.get("/api/v1/finance/financial-risks")
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert len(body["rows"]) >= 1


def test_budget_variance(finance_client) -> None:
    client, _ = finance_client
    response = client.get("/api/v1/finance/budget-variance")
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert any(r["department"] == "Brand" for r in rows)
    brand = next(r for r in rows if r["department"] == "Brand")
    assert brand["variance"] == 2000
