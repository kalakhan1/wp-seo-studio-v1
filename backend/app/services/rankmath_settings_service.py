"""Rank Math global settings service.

Wraps the companion plugin's settings endpoints. Falls back gracefully
when the plugin is not installed, giving the UI a truthful status to show.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging import get_logger
from app.config.settings import Settings
from app.core.exceptions import AuthError, ValidationError
from app.integrations.rankmath.client import RankMathClient
from app.integrations.rankmath.exceptions import (
    RankMathCompanionMissingError,
    RankMathError,
    RankMathInactiveError,
)
from app.integrations.wordpress.auth import build_auth_headers
from app.models.connection import Connection
from app.schemas.rankmath_settings import (
    RankMathCapabilityStatus,
    RankMathSettings,
    RankMathSettingsResponse,
    RankMathSettingUpdateRequest,
    RankMathSettingsUpdateResponse,
)
from app.security import secrets as secret_store

_log = get_logger(__name__)


class RankMathSettingsService:
    """Stateless. Construct per request with settings + session."""

    def __init__(self, *, settings: Settings, session: AsyncSession) -> None:
        self._settings = settings
        self._session = session

    # --- Readiness ---------------------------------------------------------

    async def get_status(
        self, *, connection_id: int, http: Any
    ) -> RankMathCapabilityStatus:
        connection = await self._require_connection(connection_id)
        rm, _ = await self._clients(connection, http)

        try:
            status = await rm.get_status()
        except RankMathCompanionMissingError:
            return RankMathCapabilityStatus(
                plugin_available=False,
                rank_math_active=False,
                reason=(
                    "Companion plugin is not installed or not active. "
                    "Global Rank Math settings cannot be read."
                ),
            )
        except RankMathError as exc:
            return RankMathCapabilityStatus(
                plugin_available=False,
                rank_math_active=False,
                reason=exc.message,
                evidence=exc.details,
            )

        rank_math_active = bool(status.get("rank_math_active", False))
        version = str(status.get("rank_math_version", "") or "")
        reason = (
            "Companion plugin detected."
            if rank_math_active
            else "Companion plugin present but Rank Math is not active."
        )
        return RankMathCapabilityStatus(
            plugin_available=True,
            rank_math_active=rank_math_active,
            version=version,
            readable_keys=[
                "title_separator",
                "homepage_title",
                "homepage_description",
                "sitemap_enabled",
                "sitemap_include_products",
                "sitemap_include_posts",
                "sitemap_include_pages",
                "noindex_empty_category",
                "noindex_search",
                "noindex_author_archives",
                "noindex_date_archives",
                "breadcrumbs_enabled",
                "wc_remove_category_base",
                "wc_show_product_breadcrumbs",
            ],
            reason=reason,
        )

    # --- Read --------------------------------------------------------------

    async def get_settings(
        self, *, connection_id: int, http: Any
    ) -> RankMathSettingsResponse:
        connection = await self._require_connection(connection_id)
        rm, _ = await self._clients(connection, http)

        warnings: list[str] = []
        try:
            result = await rm.get_settings()
        except RankMathCompanionMissingError as exc:
            return RankMathSettingsResponse(
                settings=RankMathSettings(),
                discovered_at=datetime.now(timezone.utc).isoformat(),
                source="unavailable",
                reason=(
                    "Companion plugin is not installed or not active. "
                    "Rank Math settings cannot be read."
                ),
                warnings=[exc.message],
            )
        except RankMathInactiveError as exc:
            return RankMathSettingsResponse(
                settings=RankMathSettings(),
                discovered_at=datetime.now(timezone.utc).isoformat(),
                source="unavailable",
                reason="Rank Math is not active on this site.",
                warnings=[exc.message],
            )
        except RankMathError as exc:
            return RankMathSettingsResponse(
                settings=RankMathSettings(),
                discovered_at=datetime.now(timezone.utc).isoformat(),
                source="unavailable",
                reason=exc.message,
                warnings=[exc.message],
            )

        raw = result.get("settings") or {}
        if not isinstance(raw, dict):
            raw = {}
        settings = RankMathSettings.model_validate(raw)
        version = result.get("version", "") or ""

        return RankMathSettingsResponse(
            settings=settings,
            discovered_at=datetime.now(timezone.utc).isoformat(),
            rank_math_version=str(version),
            source="companion",
            reason="",
            warnings=warnings,
        )

    # --- Write -------------------------------------------------------------

    async def update_settings(
        self,
        *,
        connection_id: int,
        payload: RankMathSettingUpdateRequest,
        http: Any,
    ) -> RankMathSettingsUpdateResponse:
        connection = await self._require_connection(connection_id)
        rm, _ = await self._clients(connection, http)

        provided = {
            k: v
            for k, v in payload.model_dump(exclude_none=True).items()
        }
        if not provided:
            raise ValidationError("No settings provided to update.")

        try:
            result = await rm.set_settings(provided)
        except RankMathCompanionMissingError as exc:
            raise ValidationError(
                "Companion plugin is not installed or not active.",
                details=exc.details,
            ) from exc
        except RankMathInactiveError as exc:
            raise ValidationError(
                "Rank Math is not active on this site.",
                details=exc.details,
            ) from exc

        raw = result.get("settings") or {}
        if not isinstance(raw, dict):
            raw = {}
        settings = RankMathSettings.model_validate(raw)
        version = str(result.get("version", "") or "")

        return RankMathSettingsUpdateResponse(
            settings=settings,
            changed=sorted(provided.keys()),
            warnings=[],
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

    async def _clients(
        self, connection: Connection, http: Any
    ) -> tuple[RankMathClient, dict[str, str]]:
        label = connection.secret_ref or connection.label
        password = secret_store.get_secret(
            label, secret_store.FIELD_WP_APP_PASSWORD
        )
        if not password:
            raise AuthError(
                "Stored WordPress credentials are missing from the OS keyring.",
                details={"label": label},
            )
        auth_headers = build_auth_headers(
            connection.auth_method,
            connection.username,
            password,
        )
        rm = RankMathClient(
            base_url=connection.base_url,
            auth_headers=auth_headers,
            http=http,
        )
        return rm, auth_headers