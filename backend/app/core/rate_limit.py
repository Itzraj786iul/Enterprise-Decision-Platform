"""Rate limiting hooks (no-op by default — ready for gateway / Redis later)."""

from __future__ import annotations

from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RateLimitHookMiddleware(BaseHTTPMiddleware):
    """
    Placeholder middleware for future rate limiting.

    Production deployments should enforce limits at the edge (Cloudflare, Render,
    API gateway) or swap this hook for a Redis-backed limiter. This middleware
    currently passes all traffic through unchanged for backward compatibility.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Future: inspect client IP / API key and return 429 when exceeded.
        request.state.rate_limit_remaining = None
        return await call_next(request)
