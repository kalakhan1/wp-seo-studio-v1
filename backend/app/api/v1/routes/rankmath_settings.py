"""Rank Math global settings endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DBSessionDep, SettingsDep
from app.core.http_client import SafeHttpClient
from app.schemas.rankmath_settings import (
    RankMathCapabilityStatus,
    RankMathSettingsResponse,
    RankMathSettingUpdateRequest,
    RankMathSettingsUpdateResponse,
)
from app.services.rankmath_settings_service import RankMathSettingsService

router = APIRouter(prefix="/rankmath/settings", tags=["rankmath"])


def _service(
    settings: SettingsDep, session: DBSessionDep
) -> RankMathSettingsService:
    return RankMathSettingsService(settings=settings, session=session)


@router.get(
    "/status",
    response_model=RankMathCapabilityStatus,
    summary="Get Rank Math + companion plugin readiness",
)
async def get_status(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> RankMathCapabilityStatus:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.get_status(
            connection_id=connection_id, http=http
        )


@router.get(
    "",
    response_model=RankMathSettingsResponse,
    summary="Read global Rank Math settings",
)
async def get_settings(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> RankMathSettingsResponse:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.get_settings(
            connection_id=connection_id, http=http
        )


@router.put(
    "",
    response_model=RankMathSettingsUpdateResponse,
    summary="Update global Rank Math settings",
    description=(
        "Only provided fields are written. Requires `manage_options` on "
        "the WordPress user."
    ),
)
async def update_settings(
    payload: RankMathSettingUpdateRequest,
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> RankMathSettingsUpdateResponse:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.update_settings(
            connection_id=connection_id,
            payload=payload,
            http=http,
        )