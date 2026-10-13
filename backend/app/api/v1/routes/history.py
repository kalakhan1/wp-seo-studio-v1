"""Publishing history endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DBSessionDep, SettingsDep
from app.schemas.history import HistoryListResponse, HistorySummary
from app.services.history_service import HistoryService

router = APIRouter(prefix="/history", tags=["history"])


def _service(settings: SettingsDep, session: DBSessionDep) -> HistoryService:
    return HistoryService(settings=settings, session=session)


@router.get(
    "",
    response_model=HistoryListResponse,
    summary="List publish history entries",
)
async def list_entries(
    settings: SettingsDep,
    session: DBSessionDep,
    object_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    connection_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> HistoryListResponse:
    service = _service(settings, session)
    return await service.list_entries(
        object_type=object_type,
        status=status,
        connection_id=connection_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/summary",
    response_model=HistorySummary,
    summary="Summary counts",
)
async def summary(
    settings: SettingsDep,
    session: DBSessionDep,
) -> HistorySummary:
    return await _service(settings, session).summary()