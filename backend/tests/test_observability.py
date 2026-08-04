"""Observability endpoint tests."""

from __future__ import annotations


def test_metrics_endpoint(client) -> None:
    # Generate at least one request metric
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")
    body = response.text
    assert "edp_http_requests_total" in body or "http_requests_total" in body or "edp_" in body


def test_metrics_reflect_request(client) -> None:
    client.get("/liveness")
    body = client.get("/metrics").text
    assert "edp_" in body


def test_health_still_public(client) -> None:
    assert client.get("/health").status_code == 200
    assert client.get("/liveness").status_code == 200
    assert client.get("/readiness").status_code == 200


def test_openapi_includes_security_scheme(client) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    components = schema.get("components", {})
    schemes = components.get("securitySchemes", {})
    assert "BearerAuth" in schemes or "HTTPBearer" in schemes or any(
        "bearer" in str(v).lower() for v in schemes.values()
    )
    assert "tags" in schema
