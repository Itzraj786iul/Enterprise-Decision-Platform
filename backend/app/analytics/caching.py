"""Optional caching interfaces for analytics services (Redis later)."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Protocol


class AnalyticsCache(Protocol):
    """Cache backend contract — NullCache is used until Redis is enabled."""

    def get(self, key: str) -> Any | None: ...

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None: ...

    def delete(self, key: str) -> None: ...


class NullCache:
    """No-op cache used by default."""

    def get(self, key: str) -> Any | None:
        return None

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        return None

    def delete(self, key: str) -> None:
        return None


def build_cache_key(prefix: str, payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"analytics:{prefix}:{digest}"
