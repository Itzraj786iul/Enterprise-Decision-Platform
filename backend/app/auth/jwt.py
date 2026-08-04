"""JWT encode/decode utilities (no identity provider)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import Settings
from app.core.exceptions import UnauthorizedError


class JwtTokenService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def encode(
        self,
        *,
        subject: str,
        roles: list[str],
        email: str | None = None,
        extra_claims: dict[str, Any] | None = None,
        expires_minutes: int | None = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(
            minutes=expires_minutes or self.settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload: dict[str, Any] = {
            "sub": subject,
            "roles": roles,
            "iat": now,
            "exp": expire,
            "iss": self.settings.JWT_ISSUER,
        }
        if email:
            payload["email"] = email
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(
            payload,
            self.settings.JWT_SECRET_KEY,
            algorithm=self.settings.JWT_ALGORITHM,
        )

    def decode(self, token: str) -> dict[str, Any]:
        try:
            return jwt.decode(
                token,
                self.settings.JWT_SECRET_KEY,
                algorithms=[self.settings.JWT_ALGORITHM],
                issuer=self.settings.JWT_ISSUER,
                options={"require": ["exp", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise UnauthorizedError("Invalid or expired access token", details={"reason": str(exc)}) from exc
