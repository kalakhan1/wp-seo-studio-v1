"""Non-secret application settings endpoint.

Phase 1 scope: read current non-secret settings and update log level.
Everything else (mode, providers, timeouts, credentials) stays in .env.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.api.deps import SettingsDep
from app.schemas.app_settings import (
    AppSettingsResponse,
    AppSettingsUpdateRequest,
)

router = APIRouter(prefix="/app-settings", tags=["app-settings"])


def _to_response(settings: SettingsDep) -> AppSettingsResponse:
    return AppSettingsResponse(
        app_env=settings.app_env.value,
        app_mode=settings.effective_app_mode.value,
        log_level=settings.log_level,
        log_format=settings.log_format.value,
        ai_provider=settings.ai_provider or "none",
        image_search_provider=settings.image_search_provider or "none",
        http_timeout=settings.http_timeout,
        http_max_retries=settings.http_max_retries,
    )


@router.get(
    "",
    response_model=AppSettingsResponse,
    summary="Get non-secret application settings",
)
async def get_app_settings(settings: SettingsDep) -> AppSettingsResponse:
    return _to_response(settings)


@router.put(
    "",
    response_model=AppSettingsResponse,
    summary="Update non-secret application settings",
    description=(
        "Only log_level can be updated at runtime. Other settings must be "
        "changed in .env so changes stay explicit and reviewable."
    ),
)
async def update_app_settings(
    payload: AppSettingsUpdateRequest,
    settings: SettingsDep,
) -> AppSettingsResponse:
    if payload.log_level is not None:
        new_level = payload.log_level.strip().lower()
        # Update both the Settings object and the live logging level so the
        # change takes effect immediately without a restart.
        object.__setattr__(settings, "log_level", new_level)
        logging.getLogger().setLevel(new_level.upper())

    return _to_response(settings)