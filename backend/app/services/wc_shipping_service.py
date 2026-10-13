"""WooCommerce shipping zone service.

Orchestrates:
  - Zone CRUD
  - Zone locations (replace-all semantics)
  - Zone methods (add/update/delete)
  - Available method types

Design notes:
  - Preserves WooCommerce defaults. Never mutates zones not asked for.
  - Locations are replaced wholesale (WC API works that way).
  - Warnings are actionable, not decorative.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging import get_logger
from app.config.settings import Settings
from app.core.exceptions import AuthError, ValidationError
from app.integrations.woocommerce.client import WooCommerceClient
from app.models.connection import Connection
from app.schemas.wc_shipping import (
    AvailableMethodsResponse,
    MethodAddRequest,
    MethodUpdateRequest,
    WCAvailableMethod,
    WCShippingMethod,
    WCShippingZone,
    WCShippingZoneDetail,
    ZoneCreateRequest,
    ZoneListResponse,
    ZoneLocation,
    ZoneUpdateRequest,
)
from app.security import secrets as secret_store

_log = get_logger(__name__)


class WCShippingService:
    """Stateless. Construct per request with settings + session."""

    def __init__(self, *, settings: Settings, session: AsyncSession) -> None:
        self._settings = settings
        self._session = session

    # --- Zones: list / read ------------------------------------------------

    async def list_zones(
        self, *, connection_id: int, http: Any
    ) -> ZoneListResponse:
        wc = await self._wc_client(connection_id, http)
        raw = await wc.list_shipping_zones()
        return ZoneListResponse(
            items=[self._to_zone(item) for item in raw]
        )

    async def get_zone_detail(
        self, *, connection_id: int, zone_id: int, http: Any
    ) -> WCShippingZoneDetail:
        wc = await self._wc_client(connection_id, http)
        zone_raw = await wc.get_shipping_zone(zone_id)
        locations_raw = await wc.list_zone_locations(zone_id)
        methods_raw = await wc.list_zone_methods(zone_id)

        return WCShippingZoneDetail(
            zone=self._to_zone(zone_raw),
            locations=[self._to_location(loc) for loc in locations_raw],
            methods=[self._to_method(m) for m in methods_raw],
        )

    # --- Zones: create / update / delete -----------------------------------

    async def create_zone(
        self,
        *,
        connection_id: int,
        payload: ZoneCreateRequest,
        http: Any,
    ) -> WCShippingZoneDetail:
        wc = await self._wc_client(connection_id, http)

        created = await wc.create_shipping_zone(
            {"name": payload.name, "order": payload.order}
        )
        zone_id = int(created.get("id", 0))
        if zone_id <= 0:
            raise ValidationError(
                "WooCommerce did not return a valid zone id.",
            )

        if payload.locations:
            await wc.update_zone_locations(
                zone_id,
                [loc.model_dump() for loc in payload.locations],
            )

        return await self.get_zone_detail(
            connection_id=connection_id, zone_id=zone_id, http=http
        )

    async def update_zone(
        self,
        *,
        connection_id: int,
        zone_id: int,
        payload: ZoneUpdateRequest,
        http: Any,
    ) -> WCShippingZoneDetail:
        wc = await self._wc_client(connection_id, http)

        zone_payload: dict[str, Any] = {}
        if payload.name is not None:
            zone_payload["name"] = payload.name
        if payload.order is not None:
            zone_payload["order"] = payload.order
        if zone_payload:
            await wc.update_shipping_zone(zone_id, zone_payload)

        if payload.locations is not None:
            await wc.update_zone_locations(
                zone_id,
                [loc.model_dump() for loc in payload.locations],
            )

        return await self.get_zone_detail(
            connection_id=connection_id, zone_id=zone_id, http=http
        )

    async def delete_zone(
        self, *, connection_id: int, zone_id: int, http: Any
    ) -> None:
        wc = await self._wc_client(connection_id, http)
        await wc.delete_shipping_zone(zone_id, force=True)

    # --- Locations ---------------------------------------------------------

    async def set_zone_locations(
        self,
        *,
        connection_id: int,
        zone_id: int,
        locations: list[ZoneLocation],
        http: Any,
    ) -> WCShippingZoneDetail:
        wc = await self._wc_client(connection_id, http)
        await wc.update_zone_locations(
            zone_id, [loc.model_dump() for loc in locations]
        )
        return await self.get_zone_detail(
            connection_id=connection_id, zone_id=zone_id, http=http
        )

    # --- Methods -----------------------------------------------------------

    async def add_method(
        self,
        *,
        connection_id: int,
        zone_id: int,
        payload: MethodAddRequest,
        http: Any,
    ) -> WCShippingMethod:
        wc = await self._wc_client(connection_id, http)
        body: dict[str, Any] = {
            "method_id": payload.method_id,
            "enabled": payload.enabled,
        }
        if payload.title is not None:
            body["title"] = payload.title
        if payload.settings:
            body["settings"] = {
                k: {"value": v} for k, v in payload.settings.items()
            }
        created = await wc.add_zone_method(zone_id, body)
        return self._to_method(created)

    async def update_method(
        self,
        *,
        connection_id: int,
        zone_id: int,
        instance_id: int,
        payload: MethodUpdateRequest,
        http: Any,
    ) -> WCShippingMethod:
        wc = await self._wc_client(connection_id, http)
        body: dict[str, Any] = {}
        if payload.title is not None:
            body["title"] = payload.title
        if payload.enabled is not None:
            body["enabled"] = payload.enabled
        if payload.settings is not None:
            body["settings"] = {
                k: {"value": v} for k, v in payload.settings.items()
            }
        if not body:
            raise ValidationError("No method fields provided to update.")
        updated = await wc.update_zone_method(zone_id, instance_id, body)
        return self._to_method(updated)

    async def delete_method(
        self,
        *,
        connection_id: int,
        zone_id: int,
        instance_id: int,
        http: Any,
    ) -> None:
        wc = await self._wc_client(connection_id, http)
        await wc.delete_zone_method(zone_id, instance_id)

    async def list_available_methods(
        self, *, connection_id: int, http: Any
    ) -> AvailableMethodsResponse:
        wc = await self._wc_client(connection_id, http)
        raw = await wc.list_available_methods()
        return AvailableMethodsResponse(
            items=[self._to_available(m) for m in raw]
        )

    # --- Internals ---------------------------------------------------------

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

    async def _wc_client(self, connection_id: int, http: Any) -> WooCommerceClient:
        c = await self._require_connection(connection_id)
        label = c.secret_ref or c.label
        wc_key = secret_store.get_secret(label, secret_store.FIELD_WC_CONSUMER_KEY)
        wc_secret = secret_store.get_secret(
            label, secret_store.FIELD_WC_CONSUMER_SECRET
        )
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

    @staticmethod
    def _to_zone(raw: dict[str, Any]) -> WCShippingZone:
        return WCShippingZone(
            id=int(raw.get("id", 0) or 0),
            name=str(raw.get("name", "") or ""),
            order=int(raw.get("order", 0) or 0),
        )

    @staticmethod
    def _to_location(raw: dict[str, Any]) -> ZoneLocation:
        return ZoneLocation(
            code=str(raw.get("code", "") or ""),
            type=str(raw.get("type", "country") or "country"),  # type: ignore[arg-type]
        )

    @staticmethod
    def _to_method(raw: dict[str, Any]) -> WCShippingMethod:
        return WCShippingMethod(
            id=int(raw["id"]) if raw.get("id") is not None else None,
            instance_id=(
                int(raw["instance_id"])
                if raw.get("instance_id") is not None
                else None
            ),
            title=str(raw.get("title", "") or ""),
            method_id=str(raw.get("method_id", "") or ""),
            method_title=str(raw.get("method_title", "") or ""),
            method_description=str(raw.get("method_description", "") or ""),
            enabled=bool(raw.get("enabled", False)),
            settings=raw.get("settings") if isinstance(raw.get("settings"), dict) else {},
        )

    @staticmethod
    def _to_available(raw: dict[str, Any]) -> WCAvailableMethod:
        return WCAvailableMethod(
            id=str(raw.get("id", "") or ""),
            title=str(raw.get("title", "") or ""),
            description=str(raw.get("description", "") or ""),
        )