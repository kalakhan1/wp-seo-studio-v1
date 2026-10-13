"""Structured logging with request ID injection and secret masking.

Uses structlog. Two output formats are supported:
  - human: colored, aligned, readable during development
  - json:  one JSON object per line, suitable for production log pipelines
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from app.config.constants import (
    MASKED_VALUE,
    SECRET_KEY_PATTERNS,
    LogFormat,
)
from app.config.settings import Settings


def _is_secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(pattern in lowered for pattern in SECRET_KEY_PATTERNS)


def _mask_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: (MASKED_VALUE if _is_secret_key(str(k)) else _mask_value(v)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_mask_value(v) for v in value]
    if isinstance(value, str) and len(value) > 512:
        # Avoid dumping huge blobs (e.g. full HTML bodies) into logs.
        return value[:256] + "...<truncated>"
    return value


def _secret_masking_processor(
    _logger: Any,
    _method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Structlog processor that masks secret-looking fields."""
    return {k: (MASKED_VALUE if _is_secret_key(str(k)) else _mask_value(v)) for k, v in event_dict.items()}


def _add_app_context(settings: Settings) -> Any:
    def processor(_logger: Any, _method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        event_dict.setdefault("app_env", settings.app_env.value)
        event_dict.setdefault("app_mode", settings.effective_app_mode.value)
        return event_dict

    return processor


def _configure_stdlib(level: str, fmt: LogFormat) -> None:
    """Configure standard library logging so third-party logs also flow through structlog."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)

    # Silence noisy libraries.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def _build_processors(settings: Settings) -> list[Any]:
    shared: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _add_app_context(settings),
        _secret_masking_processor,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if settings.log_format == LogFormat.JSON:
        shared.append(structlog.processors.JSONRenderer())
    else:
        shared.append(structlog.dev.ConsoleRenderer(colors=False))
    return shared


def configure_logging(settings: Settings) -> None:
    """Configure structlog and stdlib logging. Call once at app startup."""
    _configure_stdlib(settings.log_level, settings.log_format)

    structlog.configure(
        processors=_build_processors(settings),
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger. Use `log = get_logger(__name__)`."""
    return structlog.get_logger(name)  # type: ignore[no-any-return]
