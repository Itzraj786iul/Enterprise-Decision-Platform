"""Global exception handlers with a standard error envelope."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.schemas.common import ErrorDetail, ErrorResponse, ResponseMeta

logger = get_logger("app.errors")


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _error_body(
    *,
    code: str,
    message: str,
    request: Request,
    details: object | None = None,
) -> dict:
    payload = ErrorResponse(
        success=False,
        error=ErrorDetail(code=code, message=message, details=details),
        meta=ResponseMeta(request_id=_request_id(request)),
    )
    return payload.model_dump(mode="json")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            exc.message,
            extra={
                "request_id": _request_id(request),
                "path": request.url.path,
                "method": request.method,
                "error_type": exc.code,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(
                code=exc.code,
                message=exc.message,
                request=request,
                details=exc.details,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_body(
                code="validation_error",
                message="Request validation failed",
                request=request,
                details=exc.errors(),
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(
                code=code,
                message=str(exc.detail),
                request=request,
            ),
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.error(
            "Database error",
            extra={
                "request_id": _request_id(request),
                "path": request.url.path,
                "method": request.method,
                "error_type": "database_error",
            },
            exc_info=exc,
        )
        return JSONResponse(
            status_code=503,
            content=_error_body(
                code="database_error",
                message="A database error occurred",
                request=request,
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled server error",
            extra={
                "request_id": _request_id(request),
                "path": request.url.path,
                "method": request.method,
                "error_type": type(exc).__name__,
            },
        )
        return JSONResponse(
            status_code=500,
            content=_error_body(
                code="internal_error",
                message="An unexpected error occurred",
                request=request,
            ),
        )
