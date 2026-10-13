"""Connection lifecycle: test, save, list, delete, discover.

Secrets live only in the OS keyring (see app.security.secrets). The
database stores connection metadata keyed by a stable label.

Design decisions:
  - `label` is unique and is the key used for keyring lookups.
  - Renaming a label is not supported in Phase 2. Users delete and recreate.
  - HTTPS is enforced when `require_https=True`. In production, HTTPS is
    always required regardless of the flag.
  - Test-then-save: the UI first calls `test_credentials`, then calls
    `save` only if the test succeeds. Both paths hit the real site.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.core.exceptions import AppError, AuthError, ValidationError
from app.core.http_client import SafeHttpClient
from app.integrations.wordpress.capabilities import discover_capabilities
from app.integrations.wordpress.client import WordPressClient
from app.integrations.woocommerce.client import WooCommerceClient
from app.integrations.woocommerce.exceptions import WooClientError
from app.models.connection import Connection
from app.schemas.capability import CapabilityReport
from app.schemas.connection import (
    ConnectionResponse,
    ConnectionSaveRequest,
    ConnectionTestRequest,
    ConnectionTestResponse,
)
from app.security import secrets as secret_store

_log = logging.getLogger(__name__)


class ConnectionService:
    """Stateless service. Construct per request with settings + session."""

    def __init__(self, *, settings: Settings, session: AsyncSession) -> None:
        self._settings = settings
        self._session = session

    # --- Test --------------------------------------------------------------

    async def test_credentials(
        self,
        payload: ConnectionTestRequest,
        *,
        http: SafeHttpClient,
    ) -> ConnectionTestResponse:
        """Dry-run a connection. Never persists anything."""
        self._validate_url(payload.base_url, payload.require_https)

        wp_client = WordPressClient(
            base_url=payload.base_url,
            username=payload.username,
            app_password=payload.wp_app_password,
            auth_method=payload.auth_method,
            http=http,
        )

        site_info = None
        current_user = None
        warnings: list[str] = []

        try:
            site_info = await wp_client.get_site_info()
        except AppError as exc:
            return ConnectionTestResponse(
                ok=False,
                message=f"Could not reach WordPress: {exc.message}",
                warnings=[exc.message],
            )

        try:
            current_user = await wp_client.get_current_user()
        except AuthError as exc:
            return ConnectionTestResponse(
                ok=False,
                site_info=site_info,
                message="Authentication failed. Check the username and application password.",
                warnings=[exc.message],
            )
        except AppError as exc:
            return ConnectionTestResponse(
                ok=False,
                site_info=site_info,
                message=f"Could not verify credentials: {exc.message}",
                warnings=[exc.message],
            )

        # Optional WooCommerce probe
        wc_available = False
        if payload.wc_consumer_key and payload.wc_consumer_secret:
            try:
                wc = WooCommerceClient(
                    base_url=payload.base_url,
                    consumer_key=payload.wc_consumer_key,
                    consumer_secret=payload.wc_consumer_secret,
                    http=http,
                )
                wc_available = await wc.ping()
                if not wc_available:
                    warnings.append(
                        "WooCommerce REST did not respond. Check the consumer key and secret."
                    )
            except WooClientError as exc:
                warnings.append(f"WooCommerce probe failed: {exc.message}")
        else:
            warnings.append(
                "WooCommerce credentials not provided. Product and order features will be limited."
            )

        return ConnectionTestResponse(
            ok=True,
            site_info=site_info,
            current_user=current_user,
            wc_available=wc_available,
            message="Connection verified.",
            warnings=warnings,
        )

    # --- Save / list / get / delete ----------------------------------------

    async def save(
        self,
        payload: ConnectionSaveRequest,
    ) -> ConnectionResponse:
        self._validate_url(payload.base_url, payload.require_https)

        # Duplicate label guard (DB constraint also enforces this).
        existing = await self._session.execute(
            select(Connection).where(Connection.label == payload.label)
        )
        if existing.scalar_one_or_none() is not None:
            raise ValidationError(
                f"A connection labelled {payload.label!r} already exists.",
                details={"label": payload.label},
            )

        connection = Connection(
            label=payload.label,
            base_url=payload.base_url.rstrip("/"),
            username=payload.username,
            auth_method=payload.auth_method,
            secret_ref=payload.label,  # keyring lookup uses the label
            require_https=payload.require_https,
            notes=payload.notes,
        )

        self._session.add(connection)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ValidationError(
                "Could not save connection (duplicate label?).",
                details={"label": payload.label},
            ) from exc

        # Persist secrets to keyring AFTER the DB row is committed (flush
        # inside a transaction; commit happens in the caller).
        try:
            secret_store.set_secret(
                payload.label,
                secret_store.FIELD_WP_APP_PASSWORD,
                payload.wp_app_password,
            )
            if payload.wc_consumer_key:
                secret_store.set_secret(
                    payload.label,
                    secret_store.FIELD_WC_CONSUMER_KEY,
                    payload.wc_consumer_key,
                )
            if payload.wc_consumer_secret:
                secret_store.set_secret(
                    payload.label,
                    secret_store.FIELD_WC_CONSUMER_SECRET,
                    payload.wc_consumer_secret,
                )
        except RuntimeError as exc:
            await self._session.rollback()
            raise AppError(
                "Could not store credentials in OS keyring.",
                details={"error": str(exc)},
            ) from exc

        await self._session.commit()
        await self._session.refresh(connection)
        return self._to_response(connection, has_wc_credentials=bool(payload.wc_consumer_key))

    async def list_all(self) -> list[ConnectionResponse]:
        result = await self._session.execute(
            select(Connection).order_by(Connection.id.asc())
        )
        rows = result.scalars().all()
        return [self._to_response(c, has_wc_credentials=self._has_wc(c)) for c in rows]

    async def get(self, connection_id: int) -> ConnectionResponse:
        c = await self._require(connection_id)
        return self._to_response(c, has_wc_credentials=self._has_wc(c))

    async def delete(self, connection_id: int) -> None:
        c = await self._require(connection_id)
        label = c.label
        await self._session.delete(c)
        await self._session.commit()
        # Best-effort secret cleanup. Never fails the delete.
        secret_store.delete_all_for_label(label)

    # --- Verify / discover -------------------------------------------------

    async def verify(
        self,
        connection_id: int,
        *,
        http: SafeHttpClient,
    ) -> ConnectionTestResponse:
        c = await self._require(connection_id)
        payload = self._credentials_for(c)
        result = await self.test_credentials(payload, http=http)

        c.last_verified_at = datetime.now(timezone.utc)
        c.last_verified_ok = result.ok
        await self._session.commit()

        return result

    async def discover(
        self,
        connection_id: int,
        *,
        http: SafeHttpClient,
    ) -> CapabilityReport:
        c = await self._require(connection_id)
        creds = self._load_secrets(c)

        wp_client = WordPressClient(
            base_url=c.base_url,
            username=c.username,
            app_password=creds["wp_app_password"],
            auth_method=c.auth_method,
            http=http,
        )

        wc_client: WooCommerceClient | None = None
        if creds["wc_consumer_key"] and creds["wc_consumer_secret"]:
            try:
                wc_client = WooCommerceClient(
                    base_url=c.base_url,
                    consumer_key=creds["wc_consumer_key"],
                    consumer_secret=creds["wc_consumer_secret"],
                    http=http,
                )
            except AppError:
                wc_client = None

        report = await discover_capabilities(
            base_url=c.base_url,
            wp_client=wp_client,
            wc_client=wc_client,
            http=http,
            auth_headers={},
        )

        c.last_verified_at = datetime.now(timezone.utc)
        c.last_verified_ok = report.site_info is not None
        await self._session.commit()

        return report

    # --- Internals ---------------------------------------------------------

    async def _require(self, connection_id: int) -> Connection:
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

    def _validate_url(self, url: str, require_https: bool) -> None:
        if not url:
            raise ValidationError("Base URL is required.")
        if not url.startswith(("http://", "https://")):
            raise ValidationError("Base URL must start with http:// or https://.")
        if self._settings.is_production and not url.startswith("https://"):
            raise ValidationError("HTTPS is required in production.")
        if require_https and not url.startswith("https://"):
            raise ValidationError("This connection requires HTTPS.")

    def _credentials_for(self, c: Connection) -> ConnectionTestRequest:
        secrets_ = self._load_secrets(c)
        return ConnectionTestRequest(
            base_url=c.base_url,
            username=c.username,
            wp_app_password=secrets_["wp_app_password"],
            auth_method=c.auth_method,
            require_https=c.require_https,
            wc_consumer_key=secrets_["wc_consumer_key"],
            wc_consumer_secret=secrets_["wc_consumer_secret"],
        )

    def _load_secrets(self, c: Connection) -> dict[str, str]:
        label = c.secret_ref or c.label
        wp_pw = secret_store.get_secret(label, secret_store.FIELD_WP_APP_PASSWORD) or ""
        wc_ck = secret_store.get_secret(label, secret_store.FIELD_WC_CONSUMER_KEY) or ""
        wc_cs = secret_store.get_secret(label, secret_store.FIELD_WC_CONSUMER_SECRET) or ""
        if not wp_pw:
            raise AuthError(
                "Stored credentials are missing from the OS keyring.",
                details={"label": label},
            )
        return {
            "wp_app_password": wp_pw,
            "wc_consumer_key": wc_ck,
            "wc_consumer_secret": wc_cs,
        }

    def _has_wc(self, c: Connection) -> bool:
        label = c.secret_ref or c.label
        return bool(secret_store.get_secret(label, secret_store.FIELD_WC_CONSUMER_KEY))

    @staticmethod
    def _to_response(
        c: Connection,
        *,
        has_wc_credentials: bool,
    ) -> ConnectionResponse:
        return ConnectionResponse(
            id=c.id,
            label=c.label,
            base_url=c.base_url,
            username=c.username,
            auth_method=c.auth_method,
            require_https=c.require_https,
            notes=c.notes,
            has_wc_credentials=has_wc_credentials,
            last_verified_at=(
                c.last_verified_at.isoformat() if c.last_verified_at else None
            ),
            last_verified_ok=c.last_verified_ok,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )