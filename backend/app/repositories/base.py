"""Generic repository abstractions — no domain repositories yet."""

from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Holds the session and model type."""

    def __init__(self, session: Session, model: type[ModelT]) -> None:
        self.session = session
        self.model = model


class ReadOnlyRepository(BaseRepository[ModelT]):
    """Read helpers for future analytics/read models."""

    def get_by_id(self, entity_id: UUID | int | str) -> ModelT | None:
        return self.session.get(self.model, entity_id)

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        statement: Select[Any] | None = None,
    ) -> list[ModelT]:
        stmt = statement if statement is not None else select(self.model)
        stmt = stmt.offset(offset).limit(limit)
        return list(self.session.scalars(stmt).all())

    def count(self, statement: Select[Any] | None = None) -> int:
        if statement is None:
            stmt = select(func.count()).select_from(self.model)
        else:
            subquery = statement.order_by(None).subquery()
            stmt = select(func.count()).select_from(subquery)
        return int(self.session.scalar(stmt) or 0)

    def exists(self, entity_id: UUID | int | str) -> bool:
        return self.get_by_id(entity_id) is not None


class CRUDRepository(ReadOnlyRepository[ModelT]):
    """Generic create/update/delete helpers — unused by business APIs yet."""

    def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity: ModelT) -> None:
        self.session.delete(entity)
        self.session.flush()

    def soft_delete(self, entity: ModelT) -> ModelT:
        if hasattr(entity, "is_deleted"):
            entity.is_deleted = True
        if hasattr(entity, "deleted_at"):
            from datetime import datetime, timezone

            entity.deleted_at = datetime.now(timezone.utc)
        self.session.flush()
        return entity
