"""Generic service interfaces — no business logic."""

from __future__ import annotations

from typing import Generic, TypeVar
from uuid import UUID

from app.repositories.base import CRUDRepository, ReadOnlyRepository

RepoT = TypeVar("RepoT")
ModelT = TypeVar("ModelT")


class BaseService(Generic[RepoT]):
    def __init__(self, repository: RepoT) -> None:
        self.repository = repository


class ReadService(BaseService[ReadOnlyRepository[ModelT]], Generic[ModelT]):
    def get(self, entity_id: UUID | int | str) -> ModelT | None:
        return self.repository.get_by_id(entity_id)

    def list(self, *, offset: int = 0, limit: int = 50) -> list[ModelT]:
        return self.repository.list(offset=offset, limit=limit)


class CRUDService(BaseService[CRUDRepository[ModelT]], Generic[ModelT]):
    def get(self, entity_id: UUID | int | str) -> ModelT | None:
        return self.repository.get_by_id(entity_id)

    def list(self, *, offset: int = 0, limit: int = 50) -> list[ModelT]:
        return self.repository.list(offset=offset, limit=limit)

    def create(self, entity: ModelT) -> ModelT:
        return self.repository.add(entity)

    def remove(self, entity: ModelT) -> None:
        self.repository.delete(entity)
