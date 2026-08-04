"""Prometheus metrics endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Response

from app.core.config import get_settings
from app.observability.metrics import render_metrics

router = APIRouter(tags=["observability"])


@router.get(
    "/metrics",
    summary="Prometheus metrics",
    description="Exposes Prometheus text exposition format for scrapers.",
    responses={200: {"content": {"text/plain": {"example": "edp_http_requests_total 1\n"}}}},
)
def prometheus_metrics() -> Response:
    settings = get_settings()
    if not settings.METRICS_ENABLED:
        return Response(content="metrics disabled\n", media_type="text/plain", status_code=404)
    payload, content_type = render_metrics()
    return Response(content=payload, media_type=content_type)
