"""Image preset endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DBSessionDep, SettingsDep
from app.core.http_client import SafeHttpClient
from app.schemas.image_presets import (
    DiscoveredSizesResponse,
    PresetsResponse,
)
from app.services.image_presets_service import ImagePresetsService

router = APIRouter(prefix="/image-presets", tags=["image-presets"])


def _service(
    settings: SettingsDep, session: DBSessionDep
) -> ImagePresetsService:
    return ImagePresetsService(settings=settings, session=session)


@router.get(
    "",
    response_model=PresetsResponse,
    summary="List suggested and CSS presets",
)
async def list_presets(
    settings: SettingsDep,
    session: DBSessionDep,
) -> PresetsResponse:
    service = _service(settings, session)
    return await service.list_presets()


@router.get(
    "/discovered",
    response_model=DiscoveredSizesResponse,
    summary="Discover registered image sizes from WordPress",
    description=(
        "Inspects a media item on the connected site to list the sizes "
        "WordPress and active plugins have registered."
    ),
)
async def discover_registered_sizes(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
    media_id: int | None = Query(
        default=None,
        description="Optional media id. Defaults to the most recent image.",
    ),
) -> DiscoveredSizesResponse:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.discover_registered_sizes(
            connection_id=connection_id,
            media_id=media_id,
            http=http,
        )