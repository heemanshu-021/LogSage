"""Structured JSON logger using Python's standard logging."""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Merge any extra keyword args (kwargs passed via adapter)
        if hasattr(record, "_extra"):
            payload.update(record._extra)  # type: ignore[attr-defined]
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


class _KwargsAdapter(logging.LoggerAdapter):
    """Allows logger.info('msg', key=value, …) style calls."""

    def process(self, msg: str, kwargs: dict[str, Any]):  # type: ignore[override]
        extra_kw = {k: v for k, v in kwargs.items() if k not in {"exc_info", "stack_info", "stacklevel"}}
        kwargs = {k: v for k, v in kwargs.items() if k not in extra_kw}
        self.extra = extra_kw  # type: ignore[assignment]
        return msg, kwargs

    def log(self, level, msg, *args, **kwargs):  # type: ignore[override]
        extra_kw = {k: v for k, v in kwargs.items() if k not in {"exc_info", "stack_info", "stacklevel"}}
        kwargs = {k: v for k, v in kwargs.items() if k in {"exc_info", "stack_info", "stacklevel"}}
        if self.isEnabledFor(level):
            record = self.logger.makeRecord(
                self.logger.name, level, "(unknown)", 0, msg % args if args else msg, (), None
            )
            record._extra = extra_kw  # type: ignore[attr-defined]
            self.logger.handle(record)


def get_logger(name: str) -> _KwargsAdapter:
    """Return a structured JSON logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JSONFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(logging.DEBUG)
    return _KwargsAdapter(logger, {})


def configure_root_logging(level: str = "INFO") -> None:
    """Configure root logger — call once at startup."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JSONFormatter())
        root.addHandler(handler)
