"""Auth middleware and JWT enforcement tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def auth_client(monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("AUTH_DEV_TOKEN_ENABLED", "true")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-for-middleware-tests")
    monkeypatch.setenv("DATABASE_REQUIRED_ON_STARTUP", "false")

    from app.core.config import clear_settings_cache
    from app.database.session import reset_engine
    from app.main import create_app

    clear_settings_cache()
    reset_engine()
    with TestClient(create_app()) as client:
        yield client
    clear_settings_cache()
    reset_engine()


def _token(client: TestClient, roles: list[str]) -> str:
    response = client.post(
        "/api/v1/auth/dev-token",
        json={"subject": "tester", "roles": roles, "email": "t@example.com"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_anonymous_allowed_when_auth_not_required(client) -> None:
    response = client.get("/api/v1/platform/features")
    assert response.status_code == 200


def test_protected_route_requires_auth_when_enabled(auth_client) -> None:
    response = auth_client.get("/api/v1/dashboard/overview")
    assert response.status_code == 401


def test_finance_token_forbidden_on_sales(auth_client) -> None:
    token = _token(auth_client, ["finance"])
    response = auth_client.get(
        "/api/v1/sales/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    body = response.json()
    assert body["error"]["code"] == "forbidden"


def test_finance_token_allows_finance(auth_client) -> None:
    token = _token(auth_client, ["finance"])
    response = auth_client.get(
        "/api/v1/finance/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    # Handler may return 200 or empty analytics; auth must not 401/403
    assert response.status_code != 401
    assert response.status_code != 403


def test_admin_token_allows_sales(auth_client) -> None:
    token = _token(auth_client, ["admin"])
    response = auth_client.get(
        "/api/v1/sales/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code != 401
    assert response.status_code != 403


def test_invalid_token_returns_401(auth_client) -> None:
    response = auth_client.get(
        "/api/v1/dashboard/overview",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401


def test_authenticated_user_missing_permission_denied_even_if_auth_optional(client) -> None:
    # With AUTH_REQUIRED=false, anonymous is OK; wrong JWT still forbidden
    token_resp = client.post(
        "/api/v1/auth/dev-token",
        json={"roles": ["finance"]},
    )
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]
    response = client.get(
        "/api/v1/sales/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_request_timing_header(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Response-Time-Ms" in response.headers
    assert "X-Request-ID" in response.headers
