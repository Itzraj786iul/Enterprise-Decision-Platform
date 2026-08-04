"""Platform and auth utility routes (no analytics behavior changes)."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.dependencies.common import AppSettings, JwtService, OptionalUser
from app.auth.models import Role, permissions_for_roles
from app.core.exceptions import ForbiddenError
from app.platform.feature_registry import list_features
from app.schemas.common import ResponseMeta, utc_now

router = APIRouter(prefix="/api/v1", tags=["platform"])


class FeatureResponse(BaseModel):
    id: str
    route: str
    api_prefix: str | None = None
    navigation_label: str
    icon: str
    permissions: list[str]
    supported_filters: list[str]
    export_support: bool
    available: bool
    section: str
    description: str
    keywords: list[str]
    tags: list[str]


class FeaturesListResponse(BaseModel):
    features: list[FeatureResponse]
    generated_at: str = Field(default_factory=lambda: utc_now().isoformat())
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class DevTokenRequest(BaseModel):
    subject: str = "dev-user"
    email: str | None = "analyst@example.com"
    roles: list[str] = Field(default_factory=lambda: [Role.ANALYST.value])


class DevTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    roles: list[str]
    permissions: list[str]
    expires_minutes: int
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class MeResponse(BaseModel):
    id: str
    email: str | None = None
    roles: list[str]
    permissions: list[str]
    is_authenticated: bool
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


@router.get(
    "/platform/features",
    response_model=FeaturesListResponse,
    summary="List analytics feature registry",
    description="Central registry of analytics modules, permissions, filters, and availability.",
    responses={
        200: {
            "description": "Feature registry snapshot",
            "content": {
                "application/json": {
                    "example": {
                        "features": [
                            {
                                "id": "sales",
                                "route": "/sales",
                                "api_prefix": "/api/v1/sales",
                                "navigation_label": "Sales Intelligence",
                                "icon": "ShoppingCart",
                                "permissions": ["sales:read"],
                                "supported_filters": ["date", "region"],
                                "export_support": True,
                                "available": True,
                                "section": "main",
                                "description": "Commercial revenue and product performance",
                                "keywords": ["revenue"],
                                "tags": ["sales"],
                            }
                        ]
                    }
                }
            },
        }
    },
)
def platform_features(
    available_only: bool = Query(default=False),
) -> FeaturesListResponse:
    features = [
        FeatureResponse(
            id=f.id,
            route=f.route,
            api_prefix=f.api_prefix,
            navigation_label=f.navigation_label,
            icon=f.icon,
            permissions=[p.value for p in f.permissions],
            supported_filters=list(f.supported_filters),
            export_support=f.export_support,
            available=f.available,
            section=f.section,
            description=f.description,
            keywords=list(f.keywords),
            tags=list(f.tags),
        )
        for f in list_features(available_only=available_only)
    ]
    return FeaturesListResponse(features=features)


@router.get(
    "/auth/me",
    response_model=MeResponse,
    summary="Current principal",
    tags=["auth"],
)
def auth_me(user: OptionalUser) -> MeResponse:
    return MeResponse(
        id=user.id,
        email=user.email,
        roles=list(user.roles),
        permissions=list(user.permissions),
        is_authenticated=user.is_authenticated,
    )


@router.post(
    "/auth/dev-token",
    response_model=DevTokenResponse,
    summary="Issue local JWT (non-production)",
    description=(
        "Development/testing helper to mint JWTs. Disabled in production. "
        "Not an identity-provider integration."
    ),
    tags=["auth"],
    responses={
        403: {
            "description": "Dev token issuance disabled",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "forbidden",
                            "message": "Dev token issuance is disabled",
                        },
                    }
                }
            },
        }
    },
)
def issue_dev_token(
    body: DevTokenRequest,
    settings: AppSettings,
    jwt_service: JwtService,
) -> DevTokenResponse:
    if not settings.AUTH_DEV_TOKEN_ENABLED or settings.is_production:
        raise ForbiddenError("Dev token issuance is disabled")
    roles = body.roles or [Role.VIEWER.value]
    token = jwt_service.encode(subject=body.subject, roles=roles, email=body.email)
    perms = [p.value for p in permissions_for_roles(roles)]
    return DevTokenResponse(
        access_token=token,
        roles=roles,
        permissions=perms,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
