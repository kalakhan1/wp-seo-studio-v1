"""Standard error envelope returned by all API endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorBody(BaseModel):
    """Machine + human readable error body."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(
        ...,
        description="Machine-readable error code, e.g. VALIDATION_ERROR.",
        examples=["VALIDATION_ERROR"],
    )
    message: str = Field(
        ...,
        description="Human-readable message safe to show to the user.",
        examples=["Field 'title' is required."],
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional structured details. Never contains secrets.",
    )


class ErrorResponse(BaseModel):
    """Top-level error envelope."""

    model_config = ConfigDict(extra="forbid")

    error: ErrorBody
    request_id: str | None = Field(
        default=None,
        description="Correlation id for logs.",
        examples=["7f3c2a1b-8e5d-4a9e-9c1f-1b2c3d4e5f60"],
    )