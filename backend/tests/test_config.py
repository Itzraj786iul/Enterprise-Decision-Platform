"""Configuration unit tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import AppEnvironment, Settings, clear_settings_cache


def test_development_settings_defaults(settings) -> None:
    assert settings.APP_ENV == AppEnvironment.TESTING
    assert settings.is_testing is True
    assert settings.DATABASE_REQUIRED_ON_STARTUP is False
    assert settings.is_sqlite is True


def test_cors_origins_parsing() -> None:
    clear_settings_cache()
    cfg = Settings(
        APP_ENV="testing",
        CORS_ORIGINS="http://localhost:3000, http://127.0.0.1:3000",
        DATABASE_URL="sqlite:///:memory:",
        JWT_SECRET_KEY="test-secret-key",
    )
    assert cfg.cors_origins_list == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_production_rejects_weak_jwt() -> None:
    with pytest.raises(ValidationError):
        Settings(
            APP_ENV="production",
            DEBUG=False,
            JWT_SECRET_KEY="change-me-in-production",
            DATABASE_URL="postgresql+psycopg://u:p@localhost:5432/db",
        )


def test_production_rejects_debug_true() -> None:
    with pytest.raises(ValidationError):
        Settings(
            APP_ENV="production",
            DEBUG=True,
            JWT_SECRET_KEY="a-sufficiently-long-production-secret",
            DATABASE_URL="postgresql+psycopg://u:p@localhost:5432/db",
        )


def test_production_rejects_sqlite() -> None:
    with pytest.raises(ValidationError):
        Settings(
            APP_ENV="production",
            DEBUG=False,
            JWT_SECRET_KEY="a-sufficiently-long-production-secret",
            DATABASE_URL="sqlite:///:memory:",
        )


def test_production_normalizes_ssl_on_database_url() -> None:
    clear_settings_cache()
    cfg = Settings(
        APP_ENV="production",
        DEBUG=False,
        JWT_SECRET_KEY="a-sufficiently-long-production-secret-key",
        DATABASE_URL="postgresql://prod_user:strongpass@db.example.com:5432/edp",
        CORS_ORIGINS="https://app.example.com",
    )
    assert cfg.DATABASE_URL.startswith("postgresql+psycopg://")
    assert "sslmode=require" in cfg.DATABASE_URL
    assert cfg.AUTH_REQUIRED is True
    assert cfg.DATABASE_REQUIRED_ON_STARTUP is True


def test_jwt_secret_alias() -> None:
    clear_settings_cache()
    cfg = Settings(
        APP_ENV="testing",
        DATABASE_URL="sqlite:///:memory:",
        JWT_SECRET="alias-secret-value-for-tests-012345",
    )
    assert cfg.JWT_SECRET_KEY == "alias-secret-value-for-tests-012345"

