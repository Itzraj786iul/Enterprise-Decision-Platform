"""Shared Pydantic schemas for API envelopes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ResponseMeta(BaseModel):
    request_id: str | None = None
    timestamp: datetime = Field(default_factory=utc_now)


class BaseResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class PaginationMeta(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=200)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T]
    pagination: PaginationMeta
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class HealthComponent(BaseModel):
    name: str
    status: str
    details: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=utc_now)
    components: list[HealthComponent] = Field(default_factory=list)
    meta: ResponseMeta = Field(default_factory=ResponseMeta)

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    success: bool = True
    message: str
    meta: ResponseMeta = Field(default_factory=ResponseMeta)
