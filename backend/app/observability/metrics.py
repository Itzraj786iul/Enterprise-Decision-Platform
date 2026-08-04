"""Prometheus metrics registry and helpers."""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "edp_http_requests_total",
    "Total HTTP requests",
    ["method", "path_template", "status_code"],
)
REQUEST_ERRORS = Counter(
    "edp_http_errors_total",
    "Total HTTP 5xx responses and unhandled errors",
    ["method", "path_template"],
)
REQUEST_LATENCY = Histogram(
    "edp_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path_template"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
SLOW_REQUESTS = Counter(
    "edp_http_slow_requests_total",
    "Requests exceeding slow threshold",
    ["method", "path_template"],
)
AUTH_FAILURES = Counter(
    "edp_auth_failures_total",
    "Authentication / authorization failures",
    ["reason"],
)
APP_INFO = Gauge(
    "edp_app_info",
    "Application info label gauge",
    ["app_name", "version", "environment"],
)
READINESS = Gauge(
    "edp_readiness",
    "1 if application is ready to serve traffic",
)
LIVENESS = Gauge(
    "edp_liveness",
    "1 if application process is alive",
)


def normalize_path(path: str) -> str:
    """Collapse high-cardinality path segments for metric labels."""
    if path.startswith("/api/v1/"):
        parts = path.split("/")
        # /api/v1/<module>/...
        if len(parts) >= 4:
            return "/".join(parts[:4])
    if path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi"):
        return path.split("?")[0]
    return path


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST


def set_runtime_gauges(*, app_name: str, version: str, environment: str, ready: bool) -> None:
    APP_INFO.labels(app_name=app_name, version=version, environment=environment).set(1)
    LIVENESS.set(1)
    READINESS.set(1 if ready else 0)
