"""Request middleware: context, authz, metrics, cache headers, ETag."""

from __future__ import annotations

import hashlib
import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.api.dependencies.common import _user_from_authorization
from app.auth.models import AuthenticatedUser
from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.logging import get_logger
from app.observability import metrics as prom
from app.platform.feature_registry import required_permissions_for_path

logger = get_logger("app.middleware")

REQUEST_ID_HEADER = "X-Request-ID"

PUBLIC_PREFIXES = (
    "/health",
    "/liveness",
    "/readiness",
    "/database",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/platform",
    "/api/v1/auth",
)


def _is_public(path: str) -> bool:
    return any(path == p or path.startswith(f"{p}/") for p in PUBLIC_PREFIXES)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_settings()
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.db_duration_ms = 0.0

        started = time.perf_counter()
        path_template = prom.normalize_path(request.url.path)
        status_code = 500
        try:
            # Resolve user early for downstream handlers / authz
            try:
                user = _user_from_authorization(
                    request.headers.get("authorization"),
                    settings,
                )
            except UnauthorizedError as exc:
                prom.AUTH_FAILURES.labels(reason="invalid_token").inc()
                return JSONResponse(
                    status_code=401,
                    content={
                        "success": False,
                        "error": {"code": exc.code, "message": exc.message, "details": exc.details},
                    },
                    headers={REQUEST_ID_HEADER: request_id},
                )
            request.state.user = user

            # Permission middleware — does not modify route handlers
            if not _is_public(request.url.path) and request.method.upper() not in {"OPTIONS", "HEAD"}:
                required = required_permissions_for_path(request.url.path)
                if required:
                    if settings.AUTH_REQUIRED and not user.is_authenticated:
                        prom.AUTH_FAILURES.labels(reason="unauthenticated").inc()
                        return JSONResponse(
                            status_code=401,
                            content={
                                "success": False,
                                "error": {
                                    "code": "unauthorized",
                                    "message": "Authentication required",
                                    "details": None,
                                },
                            },
                            headers={REQUEST_ID_HEADER: request_id},
                        )
                    if user.is_authenticated:
                        missing = [p.value for p in required if not user.has_permission(p)]
                        if missing:
                            prom.AUTH_FAILURES.labels(reason="forbidden").inc()
                            return JSONResponse(
                                status_code=403,
                                content={
                                    "success": False,
                                    "error": {
                                        "code": "forbidden",
                                        "message": "Insufficient permissions",
                                        "details": {
                                            "required": [p.value for p in required],
                                            "missing": missing,
                                        },
                                    },
                                },
                                headers={REQUEST_ID_HEADER: request_id},
                            )

            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            duration_ms = (time.perf_counter() - started) * 1000
            prom.REQUEST_ERRORS.labels(method=request.method, path_template=path_template).inc()
            logger.exception(
                "Unhandled exception during request",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "duration_ms": round(duration_ms, 2),
                    "db_duration_ms": round(getattr(request.state, "db_duration_ms", 0.0), 2),
                    "error_type": "unhandled",
                },
            )
            raise

        duration_s = time.perf_counter() - started
        duration_ms = duration_s * 1000
        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

        # Structured request metrics
        prom.REQUEST_COUNT.labels(
            method=request.method,
            path_template=path_template,
            status_code=str(status_code),
        ).inc()
        prom.REQUEST_LATENCY.labels(method=request.method, path_template=path_template).observe(
            duration_s
        )
        if status_code >= 500:
            prom.REQUEST_ERRORS.labels(method=request.method, path_template=path_template).inc()
        if duration_ms >= settings.SLOW_REQUEST_MS:
            prom.SLOW_REQUESTS.labels(method=request.method, path_template=path_template).inc()
            logger.warning(
                "slow request",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2),
                    "threshold_ms": settings.SLOW_REQUEST_MS,
                },
            )

        # Cache-Control + weak ETag for safe GET JSON analytics responses
        if request.method.upper() == "GET" and 200 <= status_code < 300:
            if _is_public(request.url.path) and request.url.path.startswith(("/health", "/metrics")):
                response.headers.setdefault("Cache-Control", "no-store")
            elif request.url.path.startswith("/api/v1/"):
                response.headers.setdefault(
                    "Cache-Control",
                    f"private, max-age={settings.HTTP_CACHE_MAX_AGE_SECONDS}",
                )
                body = getattr(response, "body", None)
                if body:
                    etag = 'W/"' + hashlib.sha256(body).hexdigest()[:16] + '"'
                    response.headers.setdefault("ETag", etag)
                    if_none_match = request.headers.get("if-none-match")
                    if if_none_match and if_none_match == etag:
                        return Response(
                            status_code=304,
                            headers={
                                REQUEST_ID_HEADER: request_id,
                                "ETag": etag,
                                "Cache-Control": response.headers.get("Cache-Control", "private"),
                                "X-Response-Time-Ms": f"{duration_ms:.2f}",
                            },
                        )

        logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "db_duration_ms": round(getattr(request.state, "db_duration_ms", 0.0), 2),
                "user_id": getattr(getattr(request.state, "user", None), "id", None),
            },
        )
        return response
