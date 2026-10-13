"""Internal linking endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DBSessionDep, SettingsDep
from app.core.http_client import SafeHttpClient
from app.schemas.internal_link import (
    AnchorTextCheckRequest,
    AnchorTextCheckResponse,
    SearchResponse,
    SuggestResponse,
    ValidateUrlRequest,
    ValidateUrlResponse,
)
from app.services.internal_link_service import InternalLinkService

router = APIRouter(prefix="/internal-links", tags=["internal-links"])


def _service(settings: SettingsDep, session: DBSessionDep) -> InternalLinkService:
    return InternalLinkService(settings=settings, session=session)


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Search posts, pages, and products",
    description=(
        "Search across WordPress posts, pages, and WooCommerce products. "
        "Returns real IDs, titles, and URLs from the connected site."
    ),
)
async def search(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
    q: str = Query(..., min_length=1, max_length=200),
    posts: bool = Query(default=True),
    pages: bool = Query(default=True),
    products: bool = Query(default=True),
    per_page: int = Query(default=10, ge=1, le=50),
) -> SearchResponse:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.search(
            connection_id=connection_id,
            query=q,
            include_posts=posts,
            include_pages=pages,
            include_products=products,
            per_page=per_page,
            http=http,
        )


@router.post(
    "/suggest",
    response_model=SuggestResponse,
    summary="Suggest related content",
    description=(
        "Return a short, ranked list of related posts/pages. Suggestions "
        "are advisory; the user reviews before inserting."
    ),
)
async def suggest(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
    source_title: str = Query(..., min_length=1, max_length=500),
    source_content: str = Query(default="", max_length=5000),
    exclude_ids: str = Query(default=""),
    limit: int = Query(default=10, ge=1, le=30),
) -> SuggestResponse:
    service = _service(settings, session)
    exclude = [
        int(x) for x in exclude_ids.split(",") if x.strip().isdigit()
    ]
    async with SafeHttpClient(settings) as http:
        return await service.suggest(
            connection_id=connection_id,
            source_title=source_title,
            source_content=source_content,
            exclude_ids=exclude,
            limit=limit,
            http=http,
        )


@router.post(
    "/validate-url",
    response_model=ValidateUrlResponse,
    summary="Check that a URL belongs to the connected site",
)
async def validate_url(
    payload: ValidateUrlRequest,
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> ValidateUrlResponse:
    service = _service(settings, session)
    return await service.validate_url(
        connection_id=connection_id, url=payload.url
    )


@router.post(
    "/check-anchor",
    response_model=AnchorTextCheckResponse,
    summary="Check anchor text against existing anchors",
)
async def check_anchor(
    payload: AnchorTextCheckRequest,
    settings: SettingsDep,
    session: DBSessionDep,
) -> AnchorTextCheckResponse:
    service = _service(settings, session)
    return await service.check_anchor_text(
        anchor_text=payload.anchor_text,
        existing_anchors=payload.existing_anchors,
    )