"""Database URL normalization for Neon / managed Postgres SSL."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def normalize_database_url(url: str, *, require_ssl: bool = False) -> str:
    """
    Normalize SQLAlchemy URLs for psycopg v3 and optional SSL.

    - Rewrites postgresql:// and postgres:// → postgresql+psycopg://
    - When require_ssl is True (or host looks like Neon), ensures sslmode=require
      without overriding an explicit sslmode already present.
    """
    raw = (url or "").strip()
    if not raw or raw.startswith("sqlite"):
        return raw

    lowered = raw.lower()
    if lowered.startswith("postgres://"):
        raw = "postgresql+psycopg://" + raw[len("postgres://") :]
    elif lowered.startswith("postgresql://"):
        raw = "postgresql+psycopg://" + raw[len("postgresql://") :]
    elif lowered.startswith("postgresql+psycopg2://"):
        raw = "postgresql+psycopg://" + raw[len("postgresql+psycopg2://") :]

    parts = urlsplit(raw)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    host = (parts.hostname or "").lower()
    neon_like = host.endswith(".neon.tech") or "neon.tech" in host
    if require_ssl or neon_like:
        query.setdefault("sslmode", "require")
    new_query = urlencode(query)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))
