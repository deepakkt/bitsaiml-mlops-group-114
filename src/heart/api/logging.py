"""Logging utilities for the FastAPI service."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from sys import stdout
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON for easier scraping."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        payload: Dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in (
            "request_id",
            "path",
            "method",
            "status_code",
            "duration_ms",
            "model_version",
            "run_id",
            "source",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure JSON logging to stdout."""
    handler = logging.StreamHandler(stdout)
    handler.setFormatter(JsonFormatter())

    logging.basicConfig(level=level, handlers=[handler], force=True)
    return logging.getLogger("heart.api")
