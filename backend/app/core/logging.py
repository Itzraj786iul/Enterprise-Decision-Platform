"""Structured logging configuration."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from app.core.config import Settings


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in {
                "request_id",
                "path",
                "method",
                "status_code",
                "duration_ms",
                "db_duration_ms",
                "error_type",
            }:
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(settings: Settings) -> None:
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(settings.LOG_LEVEL)

    handler = logging.StreamHandler(sys.stdout)
    if settings.LOG_JSON:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
    root.addHandler(handler)

    # Quiet noisy libraries in production-like runs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str = "app") -> logging.Logger:
    return logging.getLogger(name)
