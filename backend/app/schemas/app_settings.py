"""Schemas for non-secret application settings endpoints.

Secrets are never accepted or returned here. They live in .env or the OS
keyring and are surfaced through the connection wizard in Phase 2.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# Allowed log levels. Enforced at the schema layer so invalid values are
# rejected with 422 before reaching the handler.
LogLevel = Literal["debug", "info", "warning", "error", "critical"]


class AppSettingsResponse(BaseModel):
    """Non-secret settings visible to the UI."""

    model_config = ConfigDict(extra="forbid")

    app_env: str = Field(
        ...,
        description="Deployment environment.",
        examples=["development"],
    )
    app_mode: str = Field(
        ...,
        description="Effective runtime mode: mock or real.",
        examples=["mock"],
    )
    log_level: str = Field(
        ...,
        description="Current log level.",
        examples=["info"],
    )
    log_format: str = Field(
        ...,
        description="Current log format: human or json.",
        examples=["human"],
    )
    ai_provider: str = Field(
        ...,
        description="Configured AI provider name, or 'none'.",
        examples=["none"],
    )
    image_search_provider: str = Field(
        ...,
        description="Configured image search provider name, or 'none'.",
        examples=["none"],
    )
    http_timeout: int = Field(
        ...,
        description="HTTP timeout in seconds.",
        examples=[30],
    )
    http_max_retries: int = Field(
        ...,
        description="Max HTTP retries on transport/5xx errors.",
        examples=[3],
    )


class AppSettingsUpdateRequest(BaseModel):
    """Only a small set of non-secret settings can be changed at runtime.

    Provider names, credentials, timeouts, and mode are intentionally NOT
    editable via the API in Phase 1: they belong in .env so changes are
    explicit and reviewable.

    `log_level` is constrained to a fixed set of values at the schema layer,
    so invalid levels are rejected with a 422 before reaching the handler.
    """

    model_config = ConfigDict(extra="forbid")

    log_level: LogLevel | None = Field(
        default=None,
        description="One of: debug, info, warning, error, critical.",
        examples=["debug"],
    )