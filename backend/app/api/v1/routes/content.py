"""Content endpoints for WordPress posts and pages."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Query, status

from app.api.deps import DBSessionDep, SettingsDep
from app.core.http_client import SafeHttpClient
from app.schemas.content import (
    ContentCreateRequest,
    ContentGetResponse,
    ContentPublishResponse,
    ContentUpdateRequest,
)
from app.services.content_service import ContentService

router = APIRouter(prefix="/content", tags=["content"])


def _service(settings: SettingsDep, session: DBSessionDep) -> ContentService:
    return ContentService(settings=settings, session=session)


@router.post(
    "/post",
    response_model=ContentPublishResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a WordPress post",
)
async def create_post(
    payload: ContentCreateRequest,
    settings: SettingsDep,
    session: DBSessionDep,
) -> ContentPublishResponse:
    payload = payload.model_copy(update={"kind": "post"})
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.create(payload, http=http)


@router.post(
    "/page",
    response_model=ContentPublishResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a WordPress page",
)
async def create_page(
    payload: ContentCreateRequest,
    settings: SettingsDep,
    session: DBSessionDep,
) -> ContentPublishResponse:
    payload = payload.model_copy(update={"kind": "page"})
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.create(payload, http=http)


@router.get(
    "/{kind}/{content_id}",
    response_model=ContentGetResponse,
    summary="Read a post or page",
)
async def get_content(
    kind: Literal["post", "page"],
    content_id: int,
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> ContentGetResponse:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.get(
            kind=kind,
            wp_object_id=content_id,
            connection_id=connection_id,
            http=http,
        )


@router.put(
    "/{kind}/{content_id}",
    response_model=ContentPublishResponse,
    summary="Update a post or page",
)
async def update_content(
    kind: Literal["post", "page"],
    content_id: int,
    payload: ContentUpdateRequest,
    settings: SettingsDep,
    session: DBSessionDep,
) -> ContentPublishResponse:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.update(
            kind=kind,
            wp_object_id=content_id,
            payload=payload,
            http=http,
        )