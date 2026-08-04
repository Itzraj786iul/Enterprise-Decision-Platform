"""Health endpoint tests."""

from __future__ import annotations


def test_health(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "backend"
    assert "request_id" in body["meta"]
    assert response.headers.get("X-Request-ID")


def test_liveness(client) -> None:
    response = client.get("/liveness")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness(client) -> None:
    response = client.get("/readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert any(c["name"] == "database" for c in body["components"])


def test_database_health(client) -> None:
    response = client.get("/database")
    # SQLite in-memory should succeed for SELECT 1
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["components"][0]["name"] == "database"


def test_unknown_route_returns_standard_error(client) -> None:
    response = client.get("/definitely-missing")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "not_found"
