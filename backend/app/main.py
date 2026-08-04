"""Enterprise Decision Platform — FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.routes import customers, dashboard, finance, health, metrics, operations, platform, sales
from app.core.config import get_settings
from app.core.config_production import assert_production_ready
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware
from app.core.rate_limit import RateLimitHookMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.database.session import init_database, shutdown_database
from app.observability.metrics import set_runtime_gauges
from app.observability.tracing import configure_tracing
from app.platform.openapi import attach_openapi

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    configure_logging(settings)
    configure_tracing(settings)
    problems = assert_production_ready(settings)
    if problems:
        for problem in problems:
            logger.error("production config problem", extra={"error_type": problem})
        raise RuntimeError("Production configuration invalid: " + "; ".join(problems))
    logger.info(
        "starting application",
        extra={"error_type": settings.APP_ENV.value},
    )
    ready = True
    try:
        init_database(settings)
    except Exception:
        logger.exception("database startup validation failed")
        ready = False
        if settings.DATABASE_REQUIRED_ON_STARTUP:
            raise
    set_runtime_gauges(
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV.value,
        ready=ready or not settings.DATABASE_REQUIRED_ON_STARTUP,
    )
    yield
    shutdown_database()
    logger.info("application shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Enterprise Decision Intelligence Platform API.\n\n"
            "Read-only analytics APIs for executive, sales, customer, operations, and finance modules.\n"
            "Authentication uses Bearer JWT. OAuth/OIDC provider interfaces are prepared but not connected.\n"
            "When `AUTH_REQUIRED=false` (default outside production), existing clients remain backward compatible."
        ),
        lifespan=lifespan,
        contact={"name": "Platform Engineering"},
        license_info={"name": "Proprietary"},
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(GZipMiddleware, minimum_size=settings.GZIP_MINIMUM_SIZE)
    application.add_middleware(RateLimitHookMiddleware)
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(RequestContextMiddleware)
    register_exception_handlers(application)
    attach_openapi(application)

    application.include_router(health.router)
    application.include_router(metrics.router)
    application.include_router(platform.router)
    application.include_router(dashboard.router)
    application.include_router(sales.router)
    application.include_router(customers.router)
    application.include_router(operations.router)
    application.include_router(finance.router)

    return application


app = create_app()
