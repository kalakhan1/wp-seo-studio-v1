"""Publishing queue service.

Phase 10 scope: local visibility + control over queued jobs.
Jobs are rows in the `job_logs` table. This phase does not run a
background worker — actual job execution is out of scope. The UI can:

  - list pending / running / finished jobs
  - see progress, error, and result
  - cancel a pending job
  - retry a failed job (marks as pending again)

Runners can be added in a later iteration without changing the schema.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.core.exceptions import ValidationError
from app.models.job_log import JobLog
from app.schemas.queue import (
    QueueJobResponse,
    QueueListResponse,
    QueueSummary,
)


class QueueService:
    """Stateless. Construct per request with settings + session."""

    def __init__(self, *, settings: Settings, session: AsyncSession) -> None:
        self._settings = settings
        self._session = session

    # --- List --------------------------------------------------------------

    async def list_jobs(
        self,
        *,
        status: str | None = None,
        job_type: str | None = None,
        connection_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> QueueListResponse:
        stmt = select(JobLog)
        count_stmt = select(func.count(JobLog.id))

        if status:
            stmt = stmt.where(JobLog.status == status)
            count_stmt = count_stmt.where(JobLog.status == status)
        if job_type:
            stmt = stmt.where(JobLog.job_type == job_type)
            count_stmt = count_stmt.where(JobLog.job_type == job_type)
        if connection_id is not None:
            stmt = stmt.where(JobLog.connection_id == connection_id)
            count_stmt = count_stmt.where(JobLog.connection_id == connection_id)

        stmt = stmt.order_by(JobLog.id.desc()).limit(limit).offset(offset)

        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        total_result = await self._session.execute(count_stmt)
        total = int(total_result.scalar_one() or 0)

        return QueueListResponse(
            items=[self._to_response(r) for r in rows],
            total=total,
        )

    async def get_job(self, job_id: int) -> QueueJobResponse:
        row = await self._require(job_id)
        return self._to_response(row)

    # --- Summary -----------------------------------------------------------

    async def summary(self) -> QueueSummary:
        result = await self._session.execute(
            select(JobLog.status, func.count(JobLog.id)).group_by(JobLog.status)
        )
        rows = result.all()
        summary = QueueSummary()
        for status, count in rows:
            c = int(count)
            if status == "pending":
                summary.pending = c
            elif status == "running":
                summary.running = c
            elif status == "success":
                summary.success = c
            elif status == "failed":
                summary.failed = c
            elif status == "partial":
                summary.partial = c
            elif status == "cancelled":
                summary.cancelled = c
            elif status == "retrying":
                summary.retrying = c
        return summary

    # --- Actions -----------------------------------------------------------

    async def cancel_job(self, job_id: int) -> QueueJobResponse:
        row = await self._require(job_id)
        if row.status not in ("pending", "retrying"):
            raise ValidationError(
                "Only pending or retrying jobs can be cancelled.",
                details={"current_status": row.status},
            )
        row.status = "cancelled"
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_response(row)

    async def retry_job(self, job_id: int) -> QueueJobResponse:
        row = await self._require(job_id)
        if row.status not in ("failed", "partial", "cancelled"):
            raise ValidationError(
                "Only failed, partial, or cancelled jobs can be retried.",
                details={"current_status": row.status},
            )
        if row.attempts >= row.max_attempts:
            raise ValidationError(
                "Job has already reached its retry limit.",
                details={"attempts": row.attempts, "max_attempts": row.max_attempts},
            )
        row.status = "pending"
        row.error = None
        row.started_at = None
        row.finished_at = None
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_response(row)

    # --- Internals ---------------------------------------------------------

    async def _require(self, job_id: int) -> JobLog:
        result = await self._session.execute(
            select(JobLog).where(JobLog.id == job_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise ValidationError(
                "Job not found.",
                details={"job_id": job_id},
            )
        return row

    @staticmethod
    def _to_response(row: JobLog) -> QueueJobResponse:
        payload: dict | None = None
        if row.payload_json:
            try:
                payload = json.loads(row.payload_json)
            except Exception:  # noqa: BLE001
                payload = None
        result_data: dict | None = None
        if row.result_json:
            try:
                result_data = json.loads(row.result_json)
            except Exception:  # noqa: BLE001
                result_data = None
        return QueueJobResponse(
            id=row.id,
            job_id=row.job_id,
            job_type=row.job_type,
            status=row.status,
            progress=row.progress,
            attempts=row.attempts,
            max_attempts=row.max_attempts,
            error=row.error,
            payload=payload,
            result=result_data,
            scheduled_at=row.scheduled_at.isoformat() if row.scheduled_at else None,
            started_at=row.started_at.isoformat() if row.started_at else None,
            finished_at=row.finished_at.isoformat() if row.finished_at else None,
            connection_id=row.connection_id,
            created_at=row.created_at.isoformat(),
            updated_at=row.updated_at.isoformat(),
        )


# Silence unused import
_ = Any