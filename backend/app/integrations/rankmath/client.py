"""Rank Math client that talks to the companion plugin.

Wraps a SafeHttpClient. All HTTP goes through it with consistent timeouts,
retries, size caps, and rate limiting.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.http_client import SafeHttpClient
from app.integrations.rankmath.exceptions import (
    RankMathCompanionMissingError,
    RankMathInactiveError,
    RankMathMetaError,
)
from app.integrations.rankmath.types import RankMathMeta

COMPANION_NAMESPACE = "wp-seo-control/v1"


class RankMathClient:
    """Read/write Rank Math per-post meta and global settings via the
    companion plugin.
    """

    def __init__(
        self,
        *,
        base_url: str,
        auth_headers: dict[str, str],
        http: SafeHttpClient,
        allow_private_hosts: bool = True,
    ) -> None:
        if not base_url:
            raise RankMathCompanionMissingError("WordPress base URL is required.")
        self.base_url = base_url.rstrip("/")
        self._http = http
        self._auth = auth_headers
        self._allow_private = allow_private_hosts

    # --- Status ------------------------------------------------------------

    async def get_status(self) -> dict[str, Any]:
        url = f"{self.base_url}/wp-json/{COMPANION_NAMESPACE}/status"
        return await self._request("GET", url)

    # --- Per-post meta -----------------------------------------------------

    async def get_meta(self, post_id: int) -> RankMathMeta:
        url = f"{self.base_url}/wp-json/{COMPANION_NAMESPACE}/rankmath/meta/{post_id}"
        body = await self._request("GET", url)
        return self._parse_meta(body, url)

    async def set_meta(self, post_id: int, meta: RankMathMeta) -> RankMathMeta:
        url = f"{self.base_url}/wp-json/{COMPANION_NAMESPACE}/rankmath/meta/{post_id}"
        payload = meta.provided_fields()
        body = await self._request("POST", url, json=payload)
        return self._parse_meta(body, url)

    # --- Global settings ---------------------------------------------------

    async def get_settings(self) -> dict[str, Any]:
        url = f"{self.base_url}/wp-json/{COMPANION_NAMESPACE}/rankmath/settings"
        body = await self._request("GET", url)
        settings = body.get("settings")
        if not isinstance(settings, dict):
            raise RankMathMetaError(
                "Companion response did not include a settings object.",
                details={"url": url},
            )
        return {
            "settings": settings,
            "version": str(body.get("version", "") or ""),
        }

    async def set_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/wp-json/{COMPANION_NAMESPACE}/rankmath/settings"
        body = await self._request("POST", url, json=payload)
        settings = body.get("settings")
        if not isinstance(settings, dict):
            raise RankMathMetaError(
                "Companion response did not include a settings object.",
                details={"url": url},
            )
        return {
            "settings": settings,
            "version": str(body.get("version", "") or ""),
        }

    # --- Internals ---------------------------------------------------------

    async def _request(
        self,
        method: str,
        url: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            response = await self._http.request(
                method,
                url,
                headers=self._auth,
                json=json,
                allow_private=self._allow_private,
            )
        except httpx.HTTPError as exc:
            raise RankMathMetaError(
                "Could not reach the companion plugin.",
                details={"url": url, "error": exc.__class__.__name__},
            ) from exc

        if response.status_code == 404:
            raise RankMathCompanionMissingError(
                "Companion plugin endpoint not found.",
                details={"url": url},
            )
        if response.status_code == 409:
            raise RankMathInactiveError(
                "Rank Math is not active on this site.",
                details={"url": url},
            )
        if response.status_code in (401, 403):
            raise RankMathMetaError(
                "Not authorized to modify Rank Math for this resource.",
                details={"url": url, "status": response.status_code},
            )
        if response.status_code >= 500:
            raise RankMathMetaError(
                "Companion plugin returned a server error.",
                details={"url": url, "status": response.status_code},
            )
        if response.status_code not in (200, 201):
            detail: dict[str, Any] = {
                "url": url,
                "status": response.status_code,
            }
            try:
                b = response.json()
                if isinstance(b, dict) and "message" in b:
                    detail["companion_message"] = str(b["message"])
            except Exception:  # noqa: BLE001
                pass
            raise RankMathMetaError(
                "Companion plugin rejected the request.",
                details=detail,
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise RankMathMetaError(
                "Companion plugin returned non-JSON.",
                details={"url": url},
            ) from exc

        if not isinstance(data, dict):
            raise RankMathMetaError(
                "Companion plugin returned unexpected JSON shape.",
                details={"url": url},
            )
        return data

    @staticmethod
    def _parse_meta(body: dict[str, Any], url: str) -> RankMathMeta:
        meta = body.get("meta")
        if not isinstance(meta, dict):
            raise RankMathMetaError(
                "Companion response did not include a `meta` object.",
                details={"url": url},
            )
        return RankMathMeta.model_validate(meta)