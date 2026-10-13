"""Schemas for publishing history."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class HistoryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    object_type: str
    operation: str
    status: str
    wp_object_id: int | None = None
    permalink: str | None = None
    message: str | None = None
    idempotency_key: str | None = None
    connection_id: int | None = None
    created_at: str


class HistoryListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[HistoryEntry] = Field(default_factory=list)
    total: int = 0


class HistorySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = 0
    success: int = 0
    failed: int = 0
    partial: int = 0