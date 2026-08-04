"""OpenAPI documentation enrichment."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


ERROR_EXAMPLE = {
    "success": False,
    "error": {
        "code": "unauthorized",
        "message": "Authentication required",
        "details": None,
    },
    "meta": {"request_id": "00000000-0000-0000-0000-000000000000"},
}


def build_openapi_schema(app: FastAPI) -> dict:
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=[
            {"name": "health", "description": "Liveness, readiness, and dependency checks"},
            {"name": "dashboard", "description": "Executive dashboard read APIs"},
            {"name": "sales", "description": "Sales Intelligence read APIs"},
            {"name": "customers", "description": "Customer Intelligence read APIs"},
            {"name": "operations", "description": "Operations Intelligence read APIs"},
            {"name": "finance", "description": "Finance Intelligence read APIs"},
            {"name": "platform", "description": "Feature registry and platform metadata"},
            {"name": "auth", "description": "JWT identity helpers (OAuth-ready; no IdP yet)"},
            {"name": "observability", "description": "Metrics and operational signals"},
        ],
    )
    schema["info"]["x-logo"] = {"altText": "Enterprise Decision Platform"}
    schema["components"] = schema.get("components") or {}
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Pass `Authorization: Bearer <jwt>` issued by your IdP or `/api/v1/auth/dev-token`.",
        }
    }
    schema["components"]["examples"] = {
        "UnauthorizedError": {"summary": "Unauthorized", "value": ERROR_EXAMPLE},
        "ForbiddenError": {
            "summary": "Forbidden",
            "value": {
                "success": False,
                "error": {
                    "code": "forbidden",
                    "message": "Insufficient permissions",
                    "details": {"required": ["sales:read"], "missing": ["sales:read"]},
                },
            },
        },
    }
    # Apply bearer security optionally (documented); enforcement is middleware-controlled.
    schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return app.openapi_schema


def attach_openapi(app: FastAPI) -> None:
    def custom_openapi():
        return build_openapi_schema(app)

    app.openapi = custom_openapi  # type: ignore[method-assign]
