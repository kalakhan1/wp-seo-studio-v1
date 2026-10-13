"""Publishing queue endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DBSessionDep, SettingsDep
from app.schemas.queue import (
    QueueJobResponse,
    QueueListResponse,
    QueueSummary,
)
from app.services.queue_service import QueueService

router = APIRouter(prefix="/queue", tags=["queue"])


def _service(settings: SettingsDep, session: DBSessionDep) -> QueueService:
    return QueueService(settings=settings, session=session)


@router.get(
    "",
    response_model=QueueListResponse,
    summary="List jobs in the publishing queue",
)
async def list_jobs(
    settings: SettingsDep,
    session: DBSessionDep,
    status: str | None = Query(default=None),
    job_type: str | None = Query(default=None),
    connection_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> QueueListResponse:
    service = _service(settings, session)
    return await service.list_jobs(
        status=status,
        job_type=job_type,
        connection_id=connection_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/summary",
    response_model=QueueSummary,
    summary="Counts per status",
)
async def summary(
    settings: SettingsDep,
    session: DBSessionDep,
) -> QueueSummary:
    return await _service(settings, session).summary()


@router.get(
    "/{job_id}",
    response_model=QueueJobResponse,
    summary="Get a single job",
)
async def get_job(
    job_id: int,
    settings: SettingsDep,
    session: DBSessionDep,
) -> QueueJobResponse:
    return await _service(settings, session).get_job(job_id)


@router.post(
    "/{job_id}/cancel",
    response_model=QueueJobResponse,
    summary="Cancel a pending job",
)
async def cancel_job(
    job_id: int,
    settings: SettingsDep,
    session: DBSessionDep,
) -> QueueJobResponse:
    return await _service(settings, session).cancel_job(job_id)


@router.post(
    "/{job_id}/retry",
    response_model=QueueJobResponse,
    summary="Retry a failed job",
)
async def retry_job(
    job_id: int,
    settings: SettingsDep,
    session: DBSessionDep,
) -> QueueJobResponse:
    return await _service(settings, session).retry_job(job_id)