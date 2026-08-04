"""Abstract ORM bases for future domain models."""

from app.database.base import Base
from app.models.mixins import (
    AuditMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class TimestampedModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Abstract base with UUID PK + timestamps."""

    __abstract__ = True


class AuditedModel(TimestampedModel, AuditMixin):
    """Abstract base with audit fields."""

    __abstract__ = True


class SoftDeleteModel(AuditedModel, SoftDeleteMixin):
    """Abstract base with soft-delete support."""

    __abstract__ = True
