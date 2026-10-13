"""Publishing queue job log."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config.constants import JobStatus
from app.db.base import Base, TimestampMixin


class JobLog(Base, TimestampMixin):
    __tablename__ = "job_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Stable public job id (UUID string), exposed to the UI
    job_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    # Job kind, e.g. "publish_product", "upload_media", "run_audit"
    job_type: Mapped[str] = mapped_column(String(60), nullable=False)

    # Job status (see JobStatus enum)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=JobStatus.PENDING.value
    )

    # Progress in [0, 100]
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Attempts made so far
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Sanitized error message (no secrets)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Optional structured payload (target ids, options) as JSON text
    payload_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Optional result summary (object id, permalink, etc.) as JSON text
    result_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Scheduling
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Optional connection reference
    connection_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_job_logs_status", "status"),
        Index("ix_job_logs_job_type", "job_type"),
        Index("ix_job_logs_scheduled_at", "scheduled_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<JobLog id={self.id} job_id={self.job_id!r} "
            f"type={self.job_type!r} status={self.status!r}>"
        )