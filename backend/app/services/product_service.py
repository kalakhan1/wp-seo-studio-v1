"""Product service: create, update, get, list, delete.

Orchestrates:
  - WooCommerce REST create/update
  - Optional Rank Math meta write via companion plugin
  - Local publish history recording

Design principles mirror ContentService:
  - Truthful partial-success reporting
  - Failed operations recorded
  - No secrets in errors
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import OperationType
from app.config.settings import Settings
from app.core.exceptions import AppError, AuthError, ValidationError
from app.core.http_client import SafeHttpClient
from app.integrations.rankmath.client import RankMathClient
from app.integrations.rankmath.exceptions import (
    RankMathCompanionMissingError,
    RankMathError,
    RankMathInactiveError,
)
from app.integrations.rankmath.types import RankMathMeta
from app.integrations.wordpress.auth import build_auth_headers
from app.integrations.woocommerce.client import WooCommerceClient
from app.integrations.woocommerce.types import WCProduct
from app.models.connection import Connection
from app.models.publish_history import PublishHistory
from app.schemas.product import (
    ProductCreateRequest,
    ProductPublishResponse,
    ProductResponse,
    ProductUpdateRequest,
    ProductImageInput,
)

_log = logging.getLogger(__name__)


class ProductService:
    """Stateless service. Construct per request."""

    def __init__(self, *, settings: Settings, session: AsyncSession) -> None:
        self._settings = settings
        self._session = session

    # --- Create ------------------------------------------------------------

    async def create(
        self,
        payload: ProductCreateRequest,
        *,
        http: SafeHttpClient,
    ) -> ProductPublishResponse:
        connection = await self._require_connection(payload.connection_id)
        wc, rm_auth_headers = await self._clients(connection, http)

        try:
            product = await wc.create_product(self._build_wc_payload_create(payload))
        except AppError as exc:
            await self._record_history(
                connection_id=connection.id,
                wp_object_id=None,
                permalink=None,
                operation=OperationType.CREATE.value,
                status="failed",
                message=exc.message,
            )
            raise

        return await self._finalize(
            connection=connection,
            product=product,
            rank_math=payload.rank_math,
            rank_math_auth_headers=rm_auth_headers,
            http=http,
            is_create=True,
        )

    # --- Update ------------------------------------------------------------

    async def update(
        self,
        *,
        product_id: int,
        payload: ProductUpdateRequest,
        http: SafeHttpClient,
    ) -> ProductPublishResponse:
        connection = await self._require_connection(payload.connection_id)
        wc, rm_auth_headers = await self._clients(connection, http)

        try:
            product = await wc.update_product(
                product_id,
                self._build_wc_payload_update(payload),
            )
        except AppError as exc:
            await self._record_history(
                connection_id=connection.id,
                wp_object_id=product_id,
                permalink=None,
                operation=OperationType.UPDATE.value,
                status="failed",
                message=exc.message,
            )
            raise

        return await self._finalize(
            connection=connection,
            product=product,
            rank_math=payload.rank_math,
            rank_math_auth_headers=rm_auth_headers,
            http=http,
            is_create=False,
        )

    # --- Get ---------------------------------------------------------------

    async def get(
        self,
        *,
        product_id: int,
        connection_id: int,
        http: SafeHttpClient,
    ) -> ProductResponse:
        connection = await self._require_connection(connection_id)
        wc, rm_auth_headers = await self._clients(connection, http)

        product = await wc.get_product(product_id)

        rank_math: RankMathMeta | None = None
        rank_math_available = False
        rank_math_reason: str | None = None

        rm = RankMathClient(
            base_url=connection.base_url,
            auth_headers=rm_auth_headers,
            http=http,
        )
        try:
            rank_math = await rm.get_meta(product.id)
            rank_math_available = True
        except RankMathCompanionMissingError:
            rank_math_reason = "Companion plugin is not installed or not active."
        except RankMathInactiveError:
            rank_math_reason = "Rank Math is not active on this site."
        except RankMathError as exc:
            rank_math_reason = f"Rank Math error: {exc.message}"

        return self._to_response(product, rank_math, rank_math_available, rank_math_reason)

    # --- List --------------------------------------------------------------

    async def list(
        self,
        *,
        connection_id: int,
        http: SafeHttpClient,
        per_page: int = 20,
        page: int = 1,
        search: str | None = None,
        status: str | None = None,
    ) -> list[ProductResponse]:
        connection = await self._require_connection(connection_id)
        wc, _ = await self._clients(connection, http)
        products = await wc.list_products(
            per_page=per_page,
            page=page,
            search=search,
            status=status,
        )
        return [
            self._to_response(p, None, False, None)
            for p in products
        ]

    # --- Delete ------------------------------------------------------------

    async def delete(
        self,
        *,
        product_id: int,
        connection_id: int,
        http: SafeHttpClient,
        force: bool = False,
    ) -> None:
        connection = await self._require_connection(connection_id)
        wc, _ = await self._clients(connection, http)
        await wc.delete_product(product_id, force=force)

        await self._record_history(
            connection_id=connection.id,
            wp_object_id=product_id,
            permalink=None,
            operation=OperationType.DELETE.value,
            status="success",
            message=None,
        )

    # --- Internals ---------------------------------------------------------

    async def _finalize(
        self,
        *,
        connection: Connection,
        product: WCProduct,
        rank_math: RankMathMeta | None,
        rank_math_auth_headers: dict[str, str],
        http: SafeHttpClient,
        is_create: bool,
    ) -> ProductPublishResponse:
        rank_math_written = False
        rank_math_error: str | None = None
        warnings: list[str] = []

        if rank_math is not None and rank_math.provided_fields():
            rm = RankMathClient(
                base_url=connection.base_url,
                auth_headers=rank_math_auth_headers,
                http=http,
            )
            try:
                await rm.set_meta(product.id, rank_math)
                rank_math_written = True
            except RankMathCompanionMissingError:
                rank_math_error = (
                    "Companion plugin is not installed or not active; "
                    "Rank Math meta was not written."
                )
                warnings.append(rank_math_error)
            except RankMathInactiveError:
                rank_math_error = (
                    "Rank Math is not active on this site; meta was not written."
                )
                warnings.append(rank_math_error)
            except RankMathError as exc:
                rank_math_error = f"Rank Math write failed: {exc.message}"
                warnings.append(rank_math_error)

        partial = (
            rank_math is not None
            and not rank_math_written
            and rank_math_error is not None
        )
        operation = OperationType.CREATE.value if is_create else OperationType.UPDATE.value
        status_str = "partial" if partial else "success"

        await self._record_history(
            connection_id=connection.id,
            wp_object_id=product.id,
            permalink=product.permalink or None,
            operation=operation,
            status=status_str,
            message=rank_math_error,
        )

        message = (
            f"Product saved (ID {product.id}, status {product.status})."
            if not partial
            else (
                f"Product saved (ID {product.id}) but Rank Math meta could "
                f"not be written: {rank_math_error}"
            )
        )

        return ProductPublishResponse(
            success=True,
            partial=partial,
            wp_object_id=product.id,
            permalink=product.permalink or None,
            status=product.status,
            name=product.name,
            slug=product.slug,
            sku=product.sku,
            rank_math_written=rank_math_written,
            rank_math_error=rank_math_error,
            message=message,
            warnings=warnings,
        )

    @staticmethod
    def _build_wc_payload_create(payload: ProductCreateRequest) -> dict[str, Any]:
        wp: dict[str, Any] = {
            "name": payload.name,
            "type": payload.type,
            "status": payload.status,
            "description": payload.description,
            "short_description": payload.short_description,
        }
        if payload.slug:
            wp["slug"] = payload.slug
        if payload.sku:
            wp["sku"] = payload.sku
        if payload.regular_price:
            wp["regular_price"] = payload.regular_price
        if payload.sale_price:
            wp["sale_price"] = payload.sale_price
        if payload.date_on_sale_from:
            wp["date_on_sale_from"] = payload.date_on_sale_from
        if payload.date_on_sale_to:
            wp["date_on_sale_to"] = payload.date_on_sale_to
        wp["tax_status"] = payload.tax_status
        if payload.tax_class:
            wp["tax_class"] = payload.tax_class
        wp["manage_stock"] = payload.manage_stock
        if payload.stock_quantity is not None:
            wp["stock_quantity"] = payload.stock_quantity
        wp["stock_status"] = payload.stock_status
        wp["backorders"] = payload.backorders
        if payload.low_stock_amount is not None:
            wp["low_stock_amount"] = payload.low_stock_amount
        wp["sold_individually"] = payload.sold_individually
        if payload.weight:
            wp["weight"] = payload.weight
        dims = payload.dimensions.model_dump()
        if any(dims.values()):
            wp["dimensions"] = dims
        if payload.shipping_class:
            wp["shipping_class"] = payload.shipping_class
        if payload.category_ids:
            wp["categories"] = [{"id": cid} for cid in payload.category_ids]
        if payload.tag_ids:
            wp["tags"] = [{"id": tid} for tid in payload.tag_ids]
        if payload.images:
            wp["images"] = ProductService._serialize_images(payload.images)
        if payload.upsell_ids:
            wp["upsell_ids"] = payload.upsell_ids
        if payload.cross_sell_ids:
            wp["cross_sell_ids"] = payload.cross_sell_ids
        wp["featured"] = payload.featured
        wp["catalog_visibility"] = payload.catalog_visibility
        wp["reviews_allowed"] = payload.reviews_allowed
        if payload.purchase_note:
            wp["purchase_note"] = payload.purchase_note
        if payload.menu_order:
            wp["menu_order"] = payload.menu_order
        return wp

    @staticmethod
    def _build_wc_payload_update(payload: ProductUpdateRequest) -> dict[str, Any]:
        wp: dict[str, Any] = {}
        if payload.name is not None:
            wp["name"] = payload.name
        if payload.slug is not None:
            wp["slug"] = payload.slug
        if payload.status is not None:
            wp["status"] = payload.status
        if payload.description is not None:
            wp["description"] = payload.description
        if payload.short_description is not None:
            wp["short_description"] = payload.short_description
        if payload.sku is not None:
            wp["sku"] = payload.sku
        if payload.regular_price is not None:
            wp["regular_price"] = payload.regular_price
        if payload.sale_price is not None:
            wp["sale_price"] = payload.sale_price
        if payload.date_on_sale_from is not None:
            wp["date_on_sale_from"] = payload.date_on_sale_from
        if payload.date_on_sale_to is not None:
            wp["date_on_sale_to"] = payload.date_on_sale_to
        if payload.tax_status is not None:
            wp["tax_status"] = payload.tax_status
        if payload.tax_class is not None:
            wp["tax_class"] = payload.tax_class
        if payload.manage_stock is not None:
            wp["manage_stock"] = payload.manage_stock
        if payload.stock_quantity is not None:
            wp["stock_quantity"] = payload.stock_quantity
        if payload.stock_status is not None:
            wp["stock_status"] = payload.stock_status
        if payload.backorders is not None:
            wp["backorders"] = payload.backorders
        if payload.low_stock_amount is not None:
            wp["low_stock_amount"] = payload.low_stock_amount
        if payload.sold_individually is not None:
            wp["sold_individually"] = payload.sold_individually
        if payload.weight is not None:
            wp["weight"] = payload.weight
        if payload.dimensions is not None:
            wp["dimensions"] = payload.dimensions.model_dump()
        if payload.shipping_class is not None:
            wp["shipping_class"] = payload.shipping_class
        if payload.category_ids is not None:
            wp["categories"] = [{"id": cid} for cid in payload.category_ids]
        if payload.tag_ids is not None:
            wp["tags"] = [{"id": tid} for tid in payload.tag_ids]
        if payload.images is not None:
            wp["images"] = ProductService._serialize_images(payload.images)
        if payload.upsell_ids is not None:
            wp["upsell_ids"] = payload.upsell_ids
        if payload.cross_sell_ids is not None:
            wp["cross_sell_ids"] = payload.cross_sell_ids
        if payload.featured is not None:
            wp["featured"] = payload.featured
        if payload.catalog_visibility is not None:
            wp["catalog_visibility"] = payload.catalog_visibility
        if payload.reviews_allowed is not None:
            wp["reviews_allowed"] = payload.reviews_allowed
        if payload.purchase_note is not None:
            wp["purchase_note"] = payload.purchase_note
        if payload.menu_order is not None:
            wp["menu_order"] = payload.menu_order
        return wp

    @staticmethod
    def _serialize_images(images: list[ProductImageInput]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for img in images:
            entry: dict[str, Any] = {}
            if img.id is not None:
                entry["id"] = img.id
            if img.src:
                entry["src"] = img.src
            if img.alt:
                entry["alt"] = img.alt
            if entry:
                out.append(entry)
        return out

    async def _require_connection(self, connection_id: int) -> Connection:
        result = await self._session.execute(
            select(Connection).where(Connection.id == connection_id)
        )
        c = result.scalar_one_or_none()
        if c is None:
            raise ValidationError(
                "Connection not found.",
                details={"connection_id": connection_id},
            )
        return c

    async def _clients(
        self,
        connection: Connection,
        http: SafeHttpClient,
    ) -> tuple[WooCommerceClient, dict[str, str]]:
        label = connection.secret_ref or connection.label
        password = secret_store_get(label, "wp_app_password")
        wc_key = secret_store_get(label, "wc_consumer_key")
        wc_secret = secret_store_get(label, "wc_consumer_secret")

        if not password:
            raise AuthError(
                "Stored WordPress credentials are missing from the OS keyring.",
                details={"label": label},
            )
        if not wc_key or not wc_secret:
            raise ValidationError(
                "WooCommerce REST API keys are missing for this connection. "
                "Add them in the Connection form.",
                details={"label": label},
            )

        wc = WooCommerceClient(
            base_url=connection.base_url,
            consumer_key=wc_key,
            consumer_secret=wc_secret,
            http=http,
        )
        rm_auth_headers = build_auth_headers(
            connection.auth_method,
            connection.username,
            password,
        )
        return wc, rm_auth_headers

    async def _record_history(
        self,
        *,
        connection_id: int,
        wp_object_id: int | None,
        permalink: str | None,
        operation: str,
        status: str,
        message: str | None,
    ) -> None:
        history = PublishHistory(
            object_type="product",
            wp_object_id=wp_object_id,
            permalink=permalink,
            operation=operation,
            status=status,
            message=message,
            connection_id=connection_id,
        )
        self._session.add(history)
        try:
            await self._session.commit()
        except Exception as exc:  # noqa: BLE001
            await self._session.rollback()
            _log.warning(
                "publish_history_write_failed",
                error=exc.__class__.__name__,
            )

    @staticmethod
    def _to_response(
        product: WCProduct,
        rank_math: RankMathMeta | None,
        rank_math_available: bool,
        rank_math_reason: str | None,
    ) -> ProductResponse:
        return ProductResponse(
            id=product.id,
            name=product.name,
            slug=product.slug,
            type=product.type,
            status=product.status,
            permalink=product.permalink,
            sku=product.sku,
            price=product.price,
            regular_price=product.regular_price,
            sale_price=product.sale_price,
            description=product.description,
            short_description=product.short_description,
            featured=product.featured,
            catalog_visibility=product.catalog_visibility,
            manage_stock=product.manage_stock,
            stock_quantity=product.stock_quantity,
            stock_status=product.stock_status,
            weight=product.weight,
            dimensions=dict(product.dimensions),
            category_ids=product.category_ids(),
            tag_ids=product.tag_ids(),
            image_ids=[i.id for i in product.images if i.id is not None],
            image_urls=[i.src for i in product.images if i.src],
            menu_order=product.menu_order,
            parent_id=product.parent_id,
            rank_math_available=rank_math_available,
            rank_math=rank_math,
            rank_math_reason=rank_math_reason,
        )


def secret_store_get(label: str, field: str) -> str | None:
    """Indirection to make testing easier and avoid circular imports."""
    from app.security import secrets as secret_store

    return secret_store.get_secret(label, field)