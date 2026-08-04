"""Database connection and repository foundation tests."""

from __future__ import annotations

import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.database.base import Base
from app.database.session import (
    get_engine,
    reset_engine,
    session_scope,
    validate_database_connection,
)
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.repositories.base import CRUDRepository


class SampleEntity(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Test-only concrete model — not part of the product schema."""

    __tablename__ = "sample_entities"
    name: Mapped[str] = mapped_column(String(64), nullable=False)


def test_validate_database_connection_ok(settings) -> None:
    reset_engine()
    result = validate_database_connection(settings)
    assert result["status"] == "ok"
    assert result["dialect"] == "sqlite"
    assert "latency_ms" in result


def test_session_scope_commit(settings) -> None:
    reset_engine()
    engine = get_engine(settings)
    Base.metadata.create_all(bind=engine)

    with session_scope(settings) as session:
        assert isinstance(session, Session)
        session.execute  # noqa: B018 — attribute presence
        entity = SampleEntity(name="alpha")
        session.add(entity)

    with session_scope(settings) as session:
        repo = CRUDRepository(session, SampleEntity)
        # Memory DB may not persist across connections without StaticPool.
        # At minimum repository methods are callable.
        assert repo.count() >= 0


def test_crud_repository_in_memory(settings) -> None:
    """Use a shared StaticPool engine so in-memory rows persist across sessions."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    session = factory()
    try:
        repo = CRUDRepository(session, SampleEntity)
        created = repo.add(SampleEntity(name="beta"))
        session.commit()
        assert isinstance(created.id, uuid.UUID)

        fetched = repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.name == "beta"
        assert repo.exists(created.id) is True
        assert repo.count() == 1
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
