"""WooCommerce settings endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DBSessionDep, SettingsDep
from app.core.http_client import SafeHttpClient
from app.schemas.wc_settings import (
    StoreProfileResponse,
    WCSetting,
    WCSettingUpdateRequest,
    WCSettingsGroupResponse,
)
from app.services.wc_settings_service import WCSettingsService

router = APIRouter(prefix="/wc/settings", tags=["wc-settings"])


def _service(settings: SettingsDep, session: DBSessionDep) -> WCSettingsService:
    return WCSettingsService(settings=settings, session=session)


@router.get(
    "/groups",
    response_model=list[str],
    summary="List known settings groups",
)
async def list_groups(settings: SettingsDep, session: DBSessionDep) -> list[str]:
    return await _service(settings, session).list_groups()


@router.get(
    "/store-profile",
    response_model=StoreProfileResponse,
    summary="Get normalized store profile with completeness checklist",
)
async def get_store_profile(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> StoreProfileResponse:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.get_store_profile(
            connection_id=connection_id,
            http=http,
        )


@router.get(
    "/{group}",
    response_model=WCSettingsGroupResponse,
    summary="Get all settings in a group",
)
async def get_group(
    group: str,
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> WCSettingsGroupResponse:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.get_group(
            connection_id=connection_id,
            group=group,
            http=http,
        )


@router.get(
    "/{group}/{setting_id}",
    response_model=WCSetting,
    summary="Get a single setting",
)
async def get_setting(
    group: str,
    setting_id: str,
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> WCSetting:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.get_setting(
            connection_id=connection_id,
            group=group,
            setting_id=setting_id,
            http=http,
        )


@router.put(
    "/{group}/{setting_id}",
    response_model=WCSetting,
    summary="Update a single setting",
    description=(
        "The value must match the setting's declared type. Checkboxes "
        "accept true/false or 'yes'/'no'. Multiselects accept a list of strings."
    ),
)
async def update_setting(
    group: str,
    setting_id: str,
    payload: WCSettingUpdateRequest,
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> WCSetting:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.update_setting(
            connection_id=connection_id,
            group=group,
            setting_id=setting_id,
            value=payload.value,
            http=http,
        )