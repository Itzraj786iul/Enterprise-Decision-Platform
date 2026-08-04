"""Reusable FastAPI dependencies."""

from __future__ import annotations

import logging
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.auth.jwt import JwtTokenService
from app.auth.models import AuthenticatedUser, Permission, permissions_for_roles
from app.core.config import Settings, get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.logging import get_logger
from app.database.session import get_db_session


def get_app_settings() -> Settings:
    return get_settings()


def get_request_logger(request: Request) -> logging.LoggerAdapter:
    base = get_logger("app.request")
    request_id = getattr(request.state, "request_id", None)
    return logging.LoggerAdapter(base, {"request_id": request_id})


def get_jwt_service(settings: Annotated[Settings, Depends(get_app_settings)]) -> JwtTokenService:
    return JwtTokenService(settings)


def _user_from_authorization(
    authorization: str | None,
    settings: Settings,
) -> AuthenticatedUser:
    if not authorization:
        return AuthenticatedUser(id="anonymous", is_authenticated=False)
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedError("Authorization header must use Bearer scheme")
    claims = JwtTokenService(settings).decode(token)
    roles = tuple(str(r) for r in (claims.get("roles") or []))
    perms = tuple(p.value for p in permissions_for_roles(roles))
    return AuthenticatedUser(
        id=str(claims.get("sub")),
        email=claims.get("email"),
        roles=roles,
        permissions=perms,
        is_authenticated=True,
        token_claims=claims,
    )


def get_current_user_optional(
    request: Request,
    settings: Annotated[Settings, Depends(get_app_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> AuthenticatedUser:
    """
    Resolve identity from Bearer JWT when present.
    Anonymous user when missing (backward compatible unless AUTH_REQUIRED).
    """
    cached = getattr(request.state, "user", None)
    if isinstance(cached, AuthenticatedUser):
        return cached
    user = _user_from_authorization(authorization, settings)
    request.state.user = user
    return user


def get_current_user(
    user: Annotated[AuthenticatedUser, Depends(get_current_user_optional)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> AuthenticatedUser:
    if settings.AUTH_REQUIRED and not user.is_authenticated:
        raise UnauthorizedError("Authentication required")
    return user


def require_permissions(*required: Permission):
    """Dependency factory for handler-level permission checks (optional use)."""

    def _dependency(
        user: Annotated[AuthenticatedUser, Depends(get_current_user)],
        settings: Annotated[Settings, Depends(get_app_settings)],
    ) -> AuthenticatedUser:
        if not settings.AUTH_REQUIRED and not user.is_authenticated:
            return user
        if not user.is_authenticated:
            raise UnauthorizedError("Authentication required")
        missing = [p.value for p in required if not user.has_permission(p)]
        if missing:
            raise ForbiddenError(
                "Insufficient permissions",
                details={"required": [p.value for p in required], "missing": missing},
            )
        return user

    return _dependency


DbSession = Annotated[Session, Depends(get_db_session)]
AppSettings = Annotated[Settings, Depends(get_app_settings)]
RequestLogger = Annotated[logging.LoggerAdapter, Depends(get_request_logger)]
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
OptionalUser = Annotated[AuthenticatedUser, Depends(get_current_user_optional)]
JwtService = Annotated[JwtTokenService, Depends(get_jwt_service)]

SessionGenerator = Generator[Session, None, None]
