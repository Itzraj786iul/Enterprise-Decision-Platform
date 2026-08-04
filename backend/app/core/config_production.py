"""Production configuration helpers (validation only — no IdP)."""

from __future__ import annotations

from app.core.config import AppEnvironment, Settings, get_settings


REQUIRED_PRODUCTION_SECRETS = (
    "JWT_SECRET_KEY",
    "DATABASE_URL",
)


def assert_production_ready(settings: Settings | None = None) -> list[str]:
    """
    Return a list of blocking configuration problems for production.
    Empty list means configuration is acceptable.
    """
    cfg = settings or get_settings()
    problems: list[str] = []
    if cfg.APP_ENV != AppEnvironment.PRODUCTION:
        return problems
    try:
        cfg._validate_production_secrets()
    except ValueError as exc:
        problems.append(str(exc))
    if not cfg.AUTH_REQUIRED:
        problems.append("AUTH_REQUIRED must be enabled in production")
    if cfg.AUTH_DEV_TOKEN_ENABLED:
        problems.append("AUTH_DEV_TOKEN_ENABLED must be disabled in production")
    if cfg.DEBUG:
        problems.append("DEBUG must be false in production")
    if "sslmode=" not in cfg.DATABASE_URL.lower() and not cfg.is_sqlite:
        problems.append("DATABASE_URL must include sslmode for production Postgres")
    if not cfg.cors_origins_list:
        problems.append("CORS_ORIGINS must include at least one frontend origin")
    return problems
