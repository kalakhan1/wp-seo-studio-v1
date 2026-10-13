"""Schemas for the publishing queue."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class QueueJobResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    job_id: str
    job_type: str
    status: str
    progress: int
    attempts: int
    max_attempts: int
    error: str | None = None
    payload: dict | None = None
    result: dict | None = None
    scheduled_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    connection_id: int | None = None
    created_at: str
    updated_at: str


class QueueListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[QueueJobResponse] = Field(default_factory=list)
    total: int = 0


class QueueSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pending: int = 0
    running: int = 0
    success: int = 0
    failed: int = 0
    partial: int = 0
    cancelled: int = 0
    retrying: int = 0