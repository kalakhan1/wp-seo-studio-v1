"""Health check response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ComponentHealthSchema(BaseModel):
    """Status of a single component (database, settings, mode, etc.)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        description="Component identifier.",
        examples=["database"],
    )
    status: str = Field(
        ...,
        description="One of: ok, degraded, failed.",
        examples=["ok"],
    )
    detail: str = Field(
        default="",
        description="Human-readable explanation. No secrets.",
        examples=["reachable"],
    )


class HealthResponse(BaseModel):
    """Overall health report."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(
        ...,
        description="Overall status: ok, degraded, or failed.",
        examples=["ok"],
    )
    mode: str = Field(
        ...,
        description="Active runtime mode: mock or real.",
        examples=["mock"],
    )
    version: str = Field(
        ...,
        description="Application version.",
        examples=["0.1.0"],
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 UTC timestamp.",
        examples=["2026-10-12T10:00:00+00:00"],
    )
    components: list[ComponentHealthSchema] = Field(
        default_factory=list,
        description="Per-component health details.",
    )