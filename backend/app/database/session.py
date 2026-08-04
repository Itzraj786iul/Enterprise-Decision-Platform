"""Database engine, pooling, session lifecycle, retries, health probe."""

from __future__ import annotations

import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger("app.database")

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _build_engine(settings: Settings) -> Engine:
    if settings.is_sqlite:
        engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False},
            echo=settings.DATABASE_ECHO,
            future=True,
        )
    else:
        # Neon / managed Postgres: pool_pre_ping recovers from idle disconnects.
        # SSL is applied via DATABASE_URL sslmode (see normalize_database_url).
        connect_args: dict[str, Any] = {
            "connect_timeout": max(1, int(settings.DATABASE_HEALTHCHECK_TIMEOUT)),
        }
        engine = create_engine(
            settings.DATABASE_URL,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            pool_recycle=settings.DATABASE_POOL_RECYCLE,
            pool_pre_ping=True,
            echo=settings.DATABASE_ECHO,
            future=True,
            connect_args=connect_args,
        )

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(  # type: ignore[no-untyped-def]
        conn, cursor, statement, parameters, context, executemany
    ) -> None:
        conn.info["query_start_time"] = time.perf_counter()

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(  # type: ignore[no-untyped-def]
        conn, cursor, statement, parameters, context, executemany
    ) -> None:
        start = conn.info.pop("query_start_time", None)
        if start is None:
            return
        duration_ms = (time.perf_counter() - start) * 1000
        logger.debug(
            "db query completed",
            extra={"db_duration_ms": round(duration_ms, 2)},
        )

    return engine


def get_engine(settings: Settings | None = None) -> Engine:
    global _engine, _SessionLocal
    if _engine is None:
        cfg = settings or get_settings()
        _engine = _build_engine(cfg)
        _SessionLocal = sessionmaker(
            bind=_engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            class_=Session,
        )
    return _engine


def get_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    get_engine(settings)
    assert _SessionLocal is not None
    return _SessionLocal


def reset_engine() -> None:
    """Dispose engine — used in tests."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


def _execute_ping(engine: Engine) -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def validate_database_connection(settings: Settings | None = None) -> dict[str, Any]:
    """Connectivity check with retries. Infrastructure only (`SELECT 1`)."""
    cfg = settings or get_settings()
    engine = get_engine(cfg)
    started = time.perf_counter()
    attempts = max(cfg.DATABASE_CONNECT_RETRIES, 1)

    @retry(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(
            multiplier=cfg.DATABASE_CONNECT_RETRY_DELAY,
            min=cfg.DATABASE_CONNECT_RETRY_DELAY,
            max=8,
        ),
        reraise=True,
    )
    def _ping() -> None:
        _execute_ping(engine)

    try:
        _ping()
        latency_ms = (time.perf_counter() - started) * 1000
        return {
            "status": "ok",
            "latency_ms": round(latency_ms, 2),
            "dialect": engine.dialect.name,
        }
    except Exception as exc:  # noqa: BLE001 — return infrastructure status
        latency_ms = (time.perf_counter() - started) * 1000
        logger.error(
            "database connectivity check failed",
            extra={"error_type": type(exc).__name__, "db_duration_ms": round(latency_ms, 2)},
        )
        return {
            "status": "error",
            "latency_ms": round(latency_ms, 2),
            "dialect": engine.dialect.name,
            "error": str(exc),
        }


def init_database(settings: Settings | None = None) -> None:
    """Create engine and optionally require connectivity on startup."""
    cfg = settings or get_settings()
    get_engine(cfg)
    result = validate_database_connection(cfg)
    if cfg.DATABASE_REQUIRED_ON_STARTUP and result["status"] != "ok":
        raise RuntimeError(f"Database unavailable on startup: {result.get('error')}")
    logger.info(
        "database engine initialized",
        extra={"db_duration_ms": result.get("latency_ms")},
    )


def shutdown_database() -> None:
    """Graceful engine disposal."""
    global _engine, _SessionLocal
    if _engine is not None:
        logger.info("disposing database engine")
        _engine.dispose()
    _engine = None
    _SessionLocal = None


@contextmanager
def session_scope(settings: Settings | None = None) -> Generator[Session, None, None]:
    factory = get_session_factory(settings)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency generator."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
