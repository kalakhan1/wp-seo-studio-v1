"""Product endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, Response, status

from app.api.deps import DBSessionDep, SettingsDep
from app.core.http_client import SafeHttpClient
from app.schemas.product import (
    ProductCreateRequest,
    ProductPublishResponse,
    ProductResponse,
    ProductUpdateRequest,
    WCCategoryItem,
    WCCategoryListResponse,
    WCTagItem,
    WCTagListResponse,
)
from app.services.product_service import ProductService
from app.core.exceptions import AuthError, ValidationError
from app.integrations.woocommerce.client import WooCommerceClient
from app.models.connection import Connection
from app.security import secrets as secret_store
from sqlalchemy import select

router = APIRouter(prefix="/products", tags=["products"])


def _service(settings: SettingsDep, session: DBSessionDep) -> ProductService:
    return ProductService(settings=settings, session=session)


@router.post(
    "",
    response_model=ProductPublishResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a WooCommerce product",
)
async def create_product(
    payload: ProductCreateRequest,
    settings: SettingsDep,
    session: DBSessionDep,
) -> ProductPublishResponse:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.create(payload, http=http)


@router.get(
    "",
    response_model=list[ProductResponse],
    summary="List products",
)
async def list_products(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
    search: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    per_page: int = Query(default=20, ge=1, le=100),
    page: int = Query(default=1, ge=1),
) -> list[ProductResponse]:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.list(
            connection_id=connection_id,
            http=http,
            per_page=per_page,
            page=page,
            search=search,
            status=status_filter,
        )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get a product",
)
async def get_product(
    product_id: int,
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> ProductResponse:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.get(
            product_id=product_id,
            connection_id=connection_id,
            http=http,
        )


@router.put(
    "/{product_id}",
    response_model=ProductPublishResponse,
    summary="Update a product",
)
async def update_product(
    product_id: int,
    payload: ProductUpdateRequest,
    settings: SettingsDep,
    session: DBSessionDep,
) -> ProductPublishResponse:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.update(
            product_id=product_id,
            payload=payload,
            http=http,
        )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete a product",
)
async def delete_product(
    product_id: int,
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
    force: bool = Query(default=False),
) -> Response:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        await service.delete(
            product_id=product_id,
            connection_id=connection_id,
            http=http,
            force=force,
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Product taxonomy (categories, tags) -----------------------------------


async def _wc_client(
    session: DBSessionDep,
    connection_id: int,
    http: SafeHttpClient,
) -> WooCommerceClient:
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
    wc_key = secret_store.get_secret(label, secret_store.FIELD_WC_CONSUMER_KEY)
    wc_secret = secret_store.get_secret(label, secret_store.FIELD_WC_CONSUMER_SECRET)
    if not wc_key or not wc_secret:
        raise AuthError(
            "WooCommerce REST API keys are missing for this connection.",
            details={"label": label},
        )
    return WooCommerceClient(
        base_url=c.base_url,
        consumer_key=wc_key,
        consumer_secret=wc_secret,
        http=http,
    )


@router.get(
    "/taxonomies/categories",
    response_model=WCCategoryListResponse,
    summary="List product categories",
)
async def list_product_categories(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
    search: str | None = Query(default=None),
    per_page: int = Query(default=100, ge=1, le=100),
) -> WCCategoryListResponse:
    async with SafeHttpClient(settings) as http:
        wc = await _wc_client(session, connection_id, http)
        cats = await wc.list_product_categories(per_page=per_page, search=search)
    return WCCategoryListResponse(
        items=[
            WCCategoryItem(
                id=c.id,
                name=c.name,
                slug=c.slug,
                parent=c.parent,
                count=c.count,
            )
            for c in cats
        ]
    )


@router.get(
    "/taxonomies/tags",
    response_model=WCTagListResponse,
    summary="List product tags",
)
async def list_product_tags(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
    search: str | None = Query(default=None),
    per_page: int = Query(default=100, ge=1, le=100),
) -> WCTagListResponse:
    async with SafeHttpClient(settings) as http:
        wc = await _wc_client(session, connection_id, http)
        tags = await wc.list_product_tags(per_page=per_page, search=search)
    return WCTagListResponse(
        items=[
            WCTagItem(id=t.id, name=t.name, slug=t.slug, count=t.count)
            for t in tags
        ]
    )