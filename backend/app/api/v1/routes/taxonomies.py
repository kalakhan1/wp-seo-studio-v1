"""Taxonomy endpoints: categories and tags.

Read-only. Writing taxonomies is intentionally out of Phase 3 scope —
creating new categories should happen deliberately, not as a side effect
of publishing content.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DBSessionDep, SettingsDep
from app.core.exceptions import AuthError, ValidationError
from app.core.http_client import SafeHttpClient
from app.integrations.wordpress.client import WordPressClient
from app.models.connection import Connection
from app.schemas.taxonomy import (
    CategoryListResponse,
    TagListResponse,
    category_from_wp,
    tag_from_wp,
)
from app.security import secrets as secret_store
from sqlalchemy import select

router = APIRouter(prefix="/taxonomies", tags=["taxonomies"])


async def _wp_client(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int,
    http: SafeHttpClient,
) -> WordPressClient:
    result = await session.execute(
        select(Connection).where(Connection.id == connection_id)
    )
    c = result.scalar_one_or_none()
    if c is None:
        raise ValidationError(
            "Connection not found.",
            details={"connection_id": connection_id},
        )
    label = c.secret_ref or c.label
    password = secret_store.get_secret(label, secret_store.FIELD_WP_APP_PASSWORD)
    if not password:
        raise AuthError(
            "Stored credentials are missing from the OS keyring.",
            details={"label": label},
        )
    return WordPressClient(
        base_url=c.base_url,
        username=c.username,
        app_password=password,
        auth_method=c.auth_method,
        http=http,
    )


@router.get(
    "/categories",
    response_model=CategoryListResponse,
    summary="List WordPress categories",
)
async def list_categories(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
    search: str | None = Query(default=None),
    per_page: int = Query(default=100, ge=1, le=100),
) -> CategoryListResponse:
    async with SafeHttpClient(settings) as http:
        wp = await _wp_client(settings, session, connection_id, http)
        cats = await wp.list_categories(per_page=per_page, search=search)
    return CategoryListResponse(items=[category_from_wp(c) for c in cats])


@router.get(
    "/tags",
    response_model=TagListResponse,
    summary="List WordPress tags",
)
async def list_tags(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
    search: str | None = Query(default=None),
    per_page: int = Query(default=100, ge=1, le=100),
) -> TagListResponse:
    async with SafeHttpClient(settings) as http:
        wp = await _wp_client(settings, session, connection_id, http)
        tags = await wp.list_tags(per_page=per_page, search=search)
    return TagListResponse(items=[tag_from_wp(t) for t in tags])