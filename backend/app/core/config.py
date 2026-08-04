"""Application settings with environment-specific validation."""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.database_url import normalize_database_url


class AppEnvironment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    APP_NAME: str = "Enterprise Decision Platform API"
    APP_VERSION: str = "0.1.0"
    APP_ENV: AppEnvironment = Field(
        default=AppEnvironment.DEVELOPMENT,
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"),
    )
    DEBUG: bool = True

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = ""

    # Database
    DATABASE_URL: str = (
        "postgresql+psycopg://user:password@localhost:5432/enterprise_decision"
    )
    DATABASE_SSL_REQUIRE: bool = False
    """When true (or Neon host), ensure sslmode=require on DATABASE_URL."""
    DATABASE_POOL_SIZE: int = Field(default=5, ge=1, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(default=10, ge=0, le=100)
    DATABASE_POOL_TIMEOUT: int = Field(default=30, ge=1)
    DATABASE_POOL_RECYCLE: int = Field(default=1800, ge=60)
    DATABASE_ECHO: bool = False
    DATABASE_CONNECT_RETRIES: int = Field(default=3, ge=0, le=20)
    DATABASE_CONNECT_RETRY_DELAY: float = Field(default=1.0, ge=0.1)
    DATABASE_REQUIRED_ON_STARTUP: bool = False
    DATABASE_HEALTHCHECK_TIMEOUT: float = Field(default=3.0, ge=0.5)

    # Analytics (read-only views)
    ANALYTICS_SCHEMA: str = "analytics"
    ANALYTICS_VIEW_OVERRIDES: str = ""
    """Comma-separated logical_key=physical_name overrides."""
    ANALYTICS_CACHE_TTL_SECONDS: int = Field(default=60, ge=0)
    ANALYTICS_MAX_PAGE_SIZE: int = Field(default=500, ge=1, le=2000)

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Auth / JWT
    JWT_SECRET_KEY: str = Field(
        default="change-me-in-production",
        validation_alias=AliasChoices("JWT_SECRET_KEY", "JWT_SECRET"),
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "edp-api"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=1)
    AUTH_REQUIRED: bool = False
    """When false, anonymous requests are allowed (backward compatible)."""
    AUTH_DEV_TOKEN_ENABLED: bool = True
    """Allow local JWT issuance endpoint outside production."""

    # Observability
    SLOW_REQUEST_MS: float = Field(default=1000.0, ge=50.0)
    METRICS_ENABLED: bool = True
    OTEL_ENABLED: bool = False
    OTEL_SERVICE_NAME: str = "edp-api"
    OTEL_CONSOLE_EXPORT: bool = False

    # HTTP performance
    GZIP_MINIMUM_SIZE: int = Field(default=500, ge=0)
    HTTP_CACHE_MAX_AGE_SECONDS: int = Field(
        default=30,
        ge=0,
        validation_alias=AliasChoices(
            "HTTP_CACHE_MAX_AGE_SECONDS",
            "CACHE_CONTROL_MAX_AGE",
        ),
    )

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_JSON: bool = True

    @field_validator("APP_ENV", mode="before")
    @classmethod
    def normalize_env(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @model_validator(mode="after")
    def validate_by_environment(self) -> Settings:
        require_ssl = self.DATABASE_SSL_REQUIRE or self.APP_ENV == AppEnvironment.PRODUCTION
        normalized = normalize_database_url(self.DATABASE_URL, require_ssl=require_ssl)
        object.__setattr__(self, "DATABASE_URL", normalized)

        if self.APP_ENV == AppEnvironment.PRODUCTION:
            self._validate_production_secrets()
            if self.DEBUG:
                raise ValueError("DEBUG must be false in production")
            if "sqlite" in self.DATABASE_URL.lower():
                raise ValueError("SQLite is not allowed in production")
            object.__setattr__(self, "AUTH_REQUIRED", True)
            object.__setattr__(self, "AUTH_DEV_TOKEN_ENABLED", False)
            object.__setattr__(self, "LOG_JSON", True)
            object.__setattr__(self, "DATABASE_REQUIRED_ON_STARTUP", True)
            object.__setattr__(self, "DATABASE_SSL_REQUIRE", True)
        if self.APP_ENV == AppEnvironment.TESTING:
            object.__setattr__(self, "DATABASE_REQUIRED_ON_STARTUP", False)
            object.__setattr__(self, "LOG_JSON", False)
            object.__setattr__(self, "OTEL_ENABLED", False)
        return self

    def _validate_production_secrets(self) -> None:
        weak_secrets = {
            "change-me-in-production",
            "secret",
            "test",
            "test-secret-key",
            "",
        }
        if self.JWT_SECRET_KEY in weak_secrets or len(self.JWT_SECRET_KEY) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be a strong secret (min 32 chars) in production"
            )
        if "user:password@" in self.DATABASE_URL:
            raise ValueError("DATABASE_URL must not use default credentials in production")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == AppEnvironment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        return self.APP_ENV == AppEnvironment.TESTING

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == AppEnvironment.PRODUCTION

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()


settings = get_settings()
