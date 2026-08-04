"""OAuth-ready interfaces — no identity provider integration yet."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class OAuthTokenSet:
    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    id_token: str | None = None
    scope: str | None = None


@dataclass(frozen=True)
class OAuthUserInfo:
    subject: str
    email: str | None = None
    name: str | None = None
    roles: tuple[str, ...] = ()
    raw: dict | None = None


class OAuthProvider(Protocol):
    """Contract for future OIDC / OAuth2 providers (Auth0, Entra ID, etc.)."""

    name: str

    def authorization_url(self, *, state: str, redirect_uri: str) -> str: ...

    def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthTokenSet: ...

    def fetch_userinfo(self, access_token: str) -> OAuthUserInfo: ...


class UnconfiguredOAuthProvider:
    """Placeholder provider that refuses to operate until configured."""

    name = "unconfigured"

    def authorization_url(self, *, state: str, redirect_uri: str) -> str:
        raise NotImplementedError("OAuth provider is not configured")

    def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthTokenSet:
        raise NotImplementedError("OAuth provider is not configured")

    def fetch_userinfo(self, access_token: str) -> OAuthUserInfo:
        raise NotImplementedError("OAuth provider is not configured")


def get_oauth_provider() -> OAuthProvider:
    return UnconfiguredOAuthProvider()
