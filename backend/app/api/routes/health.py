"""Infrastructure health endpoints — no business analytics."""

from __future__ import annotations

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.api.dependencies import AppSettings
from app.database.session import validate_database_connection
from app.schemas.common import HealthComponent, HealthResponse, ResponseMeta

router = APIRouter(tags=["health"])


def _meta(request: Request) -> ResponseMeta:
    return ResponseMeta(request_id=getattr(request.state, "request_id", None))


@router.get("/health", response_model=HealthResponse)
def health(request: Request, settings: AppSettings) -> HealthResponse:
    """Basic process liveness + metadata."""
    return HealthResponse(
        status="ok",
        service="backend",
        version=settings.APP_VERSION,
        environment=settings.APP_ENV.value,
        components=[HealthComponent(name="api", status="ok")],
        meta=_meta(request),
    )


@router.get("/liveness", response_model=HealthResponse)
def liveness(request: Request, settings: AppSettings) -> HealthResponse:
    """Kubernetes-style liveness: process is up."""
    return HealthResponse(
        status="ok",
        service="backend",
        version=settings.APP_VERSION,
        environment=settings.APP_ENV.value,
        components=[HealthComponent(name="process", status="ok")],
        meta=_meta(request),
    )


@router.get("/readiness")
def readiness(request: Request, settings: AppSettings) -> JSONResponse:
    """Ready to serve traffic if dependencies required for readiness are healthy."""
    db = validate_database_connection(settings)
    db_ok = db["status"] == "ok"
    # In testing/dev without required DB, still report degraded readiness when DB fails
    overall = "ok" if db_ok else "degraded"
    body = HealthResponse(
        status=overall,
        service="backend",
        version=settings.APP_VERSION,
        environment=settings.APP_ENV.value,
        components=[
            HealthComponent(name="api", status="ok"),
            HealthComponent(name="database", status=db["status"], details=db),
        ],
        meta=_meta(request),
    )
    code = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    # When DB is optional on startup (dev/test), return 200 with degraded for local DX
    if not settings.DATABASE_REQUIRED_ON_STARTUP and not db_ok:
        code = status.HTTP_200_OK
    return JSONResponse(status_code=code, content=body.model_dump(mode="json"))


@router.get("/database")
def database_health(request: Request, settings: AppSettings) -> JSONResponse:
    """Database infrastructure status only."""
    db = validate_database_connection(settings)
    overall = "ok" if db["status"] == "ok" else "error"
    body = HealthResponse(
        status=overall,
        service="backend",
        version=settings.APP_VERSION,
        environment=settings.APP_ENV.value,
        components=[HealthComponent(name="database", status=db["status"], details=db)],
        meta=_meta(request),
    )
    code = status.HTTP_200_OK if db["status"] == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=code, content=body.model_dump(mode="json"))
