"""Repository package — generic bases only."""

from app.repositories.base import BaseRepository, CRUDRepository, ReadOnlyRepository

__all__ = ["BaseRepository", "CRUDRepository", "ReadOnlyRepository"]
