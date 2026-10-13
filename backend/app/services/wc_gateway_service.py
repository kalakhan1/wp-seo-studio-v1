"""WooCommerce payment gateway service, focused on Cash on Delivery.

Read operations are always safe. Write operations only touch the COD
gateway in this phase. Other gateways are listed read-only.

Design:
  - Never enable a gateway without explicit user action.
  - Warnings are actionable: missing shipping zones, missing title, etc.
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
from app.schemas.wc_gateway import (
    CODSettings,
    CODStatus,
    WCGateway,
    WCGatewayListResponse,
)
from app.security import secrets as secret_store

_log = get_logger(__name__)

COD_GATEWAY_ID = "cod"


class WCGatewayService:
    """Stateless. Construct per request with settings + session."""

    def __init__(self, *, settings: Settings, session: AsyncSession) -> None:
        self._settings = settings
        self._session = session

    # --- List / read -------------------------------------------------------

    async def list_gateways(
        self,
        *,
        connection_id: int,
        http: Any,
    ) -> WCGatewayListResponse:
        wc = await self._wc_client(connection_id, http)
        raw = await wc.list_payment_gateways()
        return WCGatewayListResponse(
            items=[self._to_gateway(item) for item in raw]
        )

    async def get_gateway(
        self,
        *,
        connection_id: int,
        gateway_id: str,
        http: Any,
    ) -> WCGateway:
        wc = await self._wc_client(connection_id, http)
        raw = await wc.get_payment_gateway(gateway_id)
        return self._to_gateway(raw)

    # --- COD specific ------------------------------------------------------

    async def get_cod_status(
        self,
        *,
        connection_id: int,
        http: Any,
    ) -> CODStatus:
        wc = await self._wc_client(connection_id, http)

        available = True
        warnings: list[str] = []
        raw: dict[str, Any] = {}
        try:
            raw = await wc.get_payment_gateway(COD_GATEWAY_ID)
        except Exception as exc:  # noqa: BLE001
            available = False
            warnings.append(
                "Cash on Delivery gateway was not found on this store."
            )
            _log.info(
                "cod_gateway_missing",
                error=exc.__class__.__name__,
            )

        # Shipping zones check
        zones: list[dict[str, Any]] = []
        try:
            zones = await wc.list_shipping_zones()
        except Exception:  # noqa: BLE001
            zones = []
        shipping_zones_available = len(zones) > 0
        if not shipping_zones_available:
            warnings.append(
                "No shipping zones are configured. COD checkout may not "
                "appear for any customer."
            )

        gateway = self._to_gateway(raw) if raw else None
        enabled = bool(gateway.enabled) if gateway else False
        title = gateway.title if gateway else ""
        description = gateway.description if gateway else ""
        instructions = gateway.instructions if gateway else ""
        enable_for_virtual = gateway.enable_for_virtual if gateway else False

        if available and enabled and not title:
            warnings.append(
                "COD is enabled but the title is empty. Customers will "
                "see a blank option at checkout."
            )

        return CODStatus(
            available=available,
            enabled=enabled,
            title=title,
            description=description,
            instructions=instructions,
            enable_for_virtual=enable_for_virtual,
            shipping_zones_available=shipping_zones_available,
            warnings=warnings,
        )

    async def update_cod(
        self,
        *,
        connection_id: int,
        payload: CODSettings,
        http: Any,
    ) -> WCGateway:
        wc = await self._wc_client(connection_id, http)

        # Build the WC payload — only keys explicitly set.
        wc_payload: dict[str, Any] = {}
        if payload.enabled is not None:
            wc_payload["enabled"] = payload.enabled
        if payload.title is not None:
            wc_payload["title"] = payload.title.strip()
        if payload.description is not None:
            wc_payload["description"] = payload.description
        if payload.instructions is not None:
            wc_payload.setdefault("settings", {})["instructions"] = {
                "value": payload.instructions
            }
        if payload.enable_for_virtual is not None:
            wc_payload.setdefault("settings", {})["enable_for_virtual"] = {
                "value": "yes" if payload.enable_for_virtual else "no"
            }

        if not wc_payload:
            raise ValidationError("No COD settings provided to update.")

        updated = await wc.update_payment_gateway(COD_GATEWAY_ID, wc_payload)
        return self._to_gateway(updated)

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

    async def _wc_client(
        self,
        connection_id: int,
        http: Any,
    ) -> WooCommerceClient:
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
    def _to_gateway(raw: dict[str, Any]) -> WCGateway:
        """Map a WC gateway response to our typed model."""
        settings = raw.get("settings")
        instructions = ""
        enable_for_virtual = False
        enable_for_methods: list[str] = []

        if isinstance(settings, dict):
            ins = settings.get("instructions")
            if isinstance(ins, dict):
                instructions = str(ins.get("value", "") or "")

            efv = settings.get("enable_for_virtual")
            if isinstance(efv, dict):
                enable_for_virtual = str(efv.get("value", "")).lower() in (
                    "yes",
                    "true",
                    "1",
                )

            efm = settings.get("enable_for_methods")
            if isinstance(efm, dict):
                v = efm.get("value")
                if isinstance(v, list):
                    enable_for_methods = [str(x) for x in v]

        return WCGateway(
            id=str(raw.get("id", "")),
            title=str(raw.get("title", "") or ""),
            description=str(raw.get("description", "") or ""),
            order=int(raw.get("order", 0) or 0),
            enabled=bool(raw.get("enabled", False)),
            method_title=str(raw.get("method_title", "") or ""),
            method_description=str(raw.get("method_description", "") or ""),
            method_supports=[
                str(x) for x in (raw.get("method_supports") or [])
                if isinstance(x, str)
            ],
            instructions=instructions,
            enable_for_virtual=enable_for_virtual,
            enable_for_methods=enable_for_methods,
        )