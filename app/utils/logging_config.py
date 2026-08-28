"""
app/utils/logging_config.py
────────────────────────────
Structured logging setup with graceful fallback to standard logging.
"""
from __future__ import annotations

import logging
from typing import Any

try:
    import structlog
    _HAS_STRUCTLOG = True
except ImportError:
    _HAS_STRUCTLOG = False


class _FallbackLogger:
    """Wrapper around standard library logging to support structlog-style kwargs."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def _format_msg(self, event: str, kwargs: dict[str, Any]) -> str:
        if not kwargs:
            return event
        extra_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
        return f"{event} {extra_str}"

    def info(self, event: str, **kwargs: Any) -> None:
        self._logger.info(self._format_msg(event, kwargs))

    def debug(self, event: str, **kwargs: Any) -> None:
        self._logger.debug(self._format_msg(event, kwargs))

    def warning(self, event: str, **kwargs: Any) -> None:
        self._logger.warning(self._format_msg(event, kwargs))

    def error(self, event: str, **kwargs: Any) -> None:
        self._logger.error(self._format_msg(event, kwargs))


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging with standard processors."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=level,
    )

    if _HAS_STRUCTLOG:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(level),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )


def get_logger(name: str) -> Any:
    if _HAS_STRUCTLOG:
        return structlog.get_logger(name)
    return _FallbackLogger(logging.getLogger(name))

