"""Database URL normalization tests (Neon / SSL)."""

from __future__ import annotations

from app.core.database_url import normalize_database_url


def test_rewrites_postgres_scheme() -> None:
    url = normalize_database_url("postgres://u:p@host/db")
    assert url.startswith("postgresql+psycopg://")


def test_rewrites_postgresql_scheme() -> None:
    url = normalize_database_url("postgresql://u:p@host/db")
    assert url.startswith("postgresql+psycopg://")


def test_neon_host_gets_sslmode() -> None:
    url = normalize_database_url(
        "postgresql://u:p@ep-cool-name.us-east-2.aws.neon.tech/neondb"
    )
    assert "sslmode=require" in url
    assert url.startswith("postgresql+psycopg://")


def test_require_ssl_flag() -> None:
    url = normalize_database_url(
        "postgresql+psycopg://u:p@db.example.com/app",
        require_ssl=True,
    )
    assert "sslmode=require" in url


def test_does_not_override_explicit_sslmode() -> None:
    url = normalize_database_url(
        "postgresql://u:p@ep-x.neon.tech/db?sslmode=verify-full",
        require_ssl=True,
    )
    assert "sslmode=verify-full" in url
    assert url.count("sslmode=") == 1


def test_sqlite_untouched() -> None:
    assert normalize_database_url("sqlite:///:memory:") == "sqlite:///:memory:"
