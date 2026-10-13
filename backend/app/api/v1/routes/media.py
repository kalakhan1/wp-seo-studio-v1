"""Media endpoints: upload, list, get, update, delete."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, Query, Response, UploadFile, status

from app.api.deps import DBSessionDep, SettingsDep
from app.core.http_client import SafeHttpClient
from app.schemas.media import (
    MediaListResponse,
    MediaResponse,
    MediaUpdateRequest,
    MediaUploadResponse,
)
from app.services.media_service import MediaService

router = APIRouter(prefix="/media", tags=["media"])


def _service(settings: SettingsDep, session: DBSessionDep) -> MediaService:
    return MediaService(settings=settings, session=session)


@router.post(
    "/upload",
    response_model=MediaUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a media file to WordPress",
    description=(
        "Accepts an image, validates it, uploads it to the connected "
        "WordPress site, and caches its metadata locally."
    ),
)
async def upload_media(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Form(...),
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    alt_text: str | None = Form(default=None),
    caption: str | None = Form(default=None),
    description: str | None = Form(default=None),
) -> MediaUploadResponse:
    service = _service(settings, session)
    content = await file.read()
    async with SafeHttpClient(settings) as http:
        return await service.upload(
            connection_id=connection_id,
            filename=file.filename or "upload",
            content=content,
            declared_mime=file.content_type,
            title=title,
            alt_text=alt_text,
            caption=caption,
            description=description,
            http=http,
        )


@router.get(
    "",
    response_model=MediaListResponse,
    summary="List cached media",
)
async def list_media(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int | None = Query(default=None),
    q: str | None = Query(default=None, description="Filename search substring"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> MediaListResponse:
    service = _service(settings, session)
    return await service.list_items(
        connection_id=connection_id,
        query=q,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{media_id}",
    response_model=MediaResponse,
    summary="Get a media item",
)
async def get_media(
    media_id: int,
    settings: SettingsDep,
    session: DBSessionDep,
) -> MediaResponse:
    service = _service(settings, session)
    return await service.get(media_id)


@router.patch(
    "/{media_id}",
    response_model=MediaResponse,
    summary="Update media metadata",
    description=(
        "Updates local metadata and, by default, propagates to the "
        "WordPress media item."
    ),
)
async def update_media(
    media_id: int,
    payload: MediaUpdateRequest,
    settings: SettingsDep,
    session: DBSessionDep,
) -> MediaResponse:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.update(media_id=media_id, payload=payload, http=http)


@router.delete(
    "/{media_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete a media item",
    description=(
        "Deletes the media item on WordPress (to trash by default) and "
        "removes the local cache record."
    ),
)
async def delete_media(
    media_id: int,
    settings: SettingsDep,
    session: DBSessionDep,
    force: bool = Query(default=False),
) -> Response:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        await service.delete(media_id=media_id, http=http, force=force)
    return Response(status_code=status.HTTP_204_NO_CONTENT)