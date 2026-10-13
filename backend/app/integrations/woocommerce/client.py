"""WooCommerce REST API client.

Composes SafeHttpClient with WooCommerce Basic auth.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.exceptions import AuthError
from app.core.http_client import SafeHttpClient
from app.integrations.woocommerce.auth import build_wc_basic_auth_header
from app.integrations.woocommerce.exceptions import (
    WooAuthError,
    WooConnectionError,
    WooNotFoundError,
    WooResponseError,
)
from app.integrations.woocommerce.types import (
    WCCategory,
    WCProduct,
    WCTag,
)


class WooCommerceClient:
    """Client for a single WooCommerce store."""

    def __init__(
        self,
        *,
        base_url: str,
        consumer_key: str,
        consumer_secret: str,
        http: SafeHttpClient,
        allow_private_hosts: bool = True,
    ) -> None:
        if not base_url:
            raise WooAuthError("WooCommerce base URL is required.")
        try:
            auth_header = build_wc_basic_auth_header(
                consumer_key,
                consumer_secret,
            )
        except AuthError as exc:
            raise WooAuthError(str(exc)) from exc

        self.base_url = base_url.rstrip("/")
        self._http = http
        self._allow_private = allow_private_hosts
        self._auth_headers = {"Authorization": auth_header}

    # --- Products ----------------------------------------------------------

    async def ping(self) -> bool:
        try:
            await self._get_json("/wp-json/wc/v3/products", params={"per_page": 1})
            return True
        except (WooAuthError, WooNotFoundError):
            return False

    async def list_products(
        self,
        *,
        per_page: int = 10,
        page: int = 1,
        search: str | None = None,
        status: str | None = None,
    ) -> list[WCProduct]:
        params: dict[str, Any] = {"per_page": per_page, "page": page}
        if search:
            params["search"] = search
        if status:
            params["status"] = status
        data = await self._get_json("/wp-json/wc/v3/products", params=params)
        if not isinstance(data, list):
            return []
        return [WCProduct.model_validate(item) for item in data]

    async def get_product(self, product_id: int) -> WCProduct:
        data = await self._get_json(f"/wp-json/wc/v3/products/{product_id}")
        return WCProduct.model_validate(data)

    async def create_product(self, payload: dict[str, Any]) -> WCProduct:
        data = await self._request_json(
            "POST", "/wp-json/wc/v3/products", json=payload
        )
        return WCProduct.model_validate(data)

    async def update_product(
        self, product_id: int, payload: dict[str, Any]
    ) -> WCProduct:
        data = await self._request_json(
            "PUT", f"/wp-json/wc/v3/products/{product_id}", json=payload
        )
        return WCProduct.model_validate(data)

    async def delete_product(self, product_id: int, *, force: bool = False) -> None:
        url = f"{self.base_url}/wp-json/wc/v3/products/{product_id}"
        params = {"force": "true"} if force else None
        try:
            response = await self._http.request(
                "DELETE",
                url,
                headers=self._auth_headers,
                params=params,
                allow_private=self._allow_private,
            )
        except httpx.HTTPError as exc:
            raise WooConnectionError(
                "Could not reach WooCommerce during product delete.",
                details={"url": url, "error": exc.__class__.__name__},
            ) from exc
        self._raise_for_status(response, url)

    async def list_product_categories(
        self, *, per_page: int = 100, search: str | None = None
    ) -> list[WCCategory]:
        params: dict[str, Any] = {"per_page": per_page}
        if search:
            params["search"] = search
        data = await self._get_json(
            "/wp-json/wc/v3/products/categories", params=params
        )
        if not isinstance(data, list):
            return []
        return [WCCategory.model_validate(item) for item in data]

    async def list_product_tags(
        self, *, per_page: int = 100, search: str | None = None
    ) -> list[WCTag]:
        params: dict[str, Any] = {"per_page": per_page}
        if search:
            params["search"] = search
        data = await self._get_json("/wp-json/wc/v3/products/tags", params=params)
        if not isinstance(data, list):
            return []
        return [WCTag.model_validate(item) for item in data]

    # --- Settings ----------------------------------------------------------

    async def get_settings_group(self, group: str) -> list[dict[str, Any]]:
        data = await self._get_json(f"/wp-json/wc/v3/settings/{group}")
        return data if isinstance(data, list) else []

    async def get_setting(self, group: str, setting_id: str) -> dict[str, Any]:
        data = await self._get_json(f"/wp-json/wc/v3/settings/{group}/{setting_id}")
        return data if isinstance(data, dict) else {}

    async def update_setting(
        self, group: str, setting_id: str, value: Any
    ) -> dict[str, Any]:
        data = await self._request_json(
            "PUT",
            f"/wp-json/wc/v3/settings/{group}/{setting_id}",
            json={"value": value},
        )
        return data if isinstance(data, dict) else {}

    async def list_countries(self) -> list[dict[str, Any]]:
        data = await self._get_json("/wp-json/wc/v3/data/countries")
        return data if isinstance(data, list) else []

    async def list_currencies(self) -> list[dict[str, Any]]:
        data = await self._get_json("/wp-json/wc/v3/data/currencies")
        return data if isinstance(data, list) else []

    # --- Payment gateways --------------------------------------------------

    async def list_payment_gateways(self) -> list[dict[str, Any]]:
        data = await self._get_json("/wp-json/wc/v3/payment_gateways")
        return data if isinstance(data, list) else []

    async def get_payment_gateway(self, gateway_id: str) -> dict[str, Any]:
        data = await self._get_json(f"/wp-json/wc/v3/payment_gateways/{gateway_id}")
        return data if isinstance(data, dict) else {}

    async def update_payment_gateway(
        self, gateway_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        data = await self._request_json(
            "PUT",
            f"/wp-json/wc/v3/payment_gateways/{gateway_id}",
            json=payload,
        )
        return data if isinstance(data, dict) else {}

    # --- Shipping zones ----------------------------------------------------

    async def list_shipping_zones(self) -> list[dict[str, Any]]:
        data = await self._get_json("/wp-json/wc/v3/shipping/zones")
        return data if isinstance(data, list) else []

    async def get_shipping_zone(self, zone_id: int) -> dict[str, Any]:
        data = await self._get_json(f"/wp-json/wc/v3/shipping/zones/{zone_id}")
        return data if isinstance(data, dict) else {}

    async def create_shipping_zone(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = await self._request_json(
            "POST", "/wp-json/wc/v3/shipping/zones", json=payload
        )
        return data if isinstance(data, dict) else {}

    async def update_shipping_zone(
        self, zone_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        data = await self._request_json(
            "PUT", f"/wp-json/wc/v3/shipping/zones/{zone_id}", json=payload
        )
        return data if isinstance(data, dict) else {}

    async def delete_shipping_zone(self, zone_id: int, *, force: bool = True) -> None:
        url = f"{self.base_url}/wp-json/wc/v3/shipping/zones/{zone_id}"
        params = {"force": "true"} if force else None
        try:
            response = await self._http.request(
                "DELETE",
                url,
                headers=self._auth_headers,
                params=params,
                allow_private=self._allow_private,
            )
        except httpx.HTTPError as exc:
            raise WooConnectionError(
                "Could not reach WooCommerce during zone delete.",
                details={"url": url, "error": exc.__class__.__name__},
            ) from exc
        self._raise_for_status(response, url)

    async def list_zone_locations(self, zone_id: int) -> list[dict[str, Any]]:
        data = await self._get_json(
            f"/wp-json/wc/v3/shipping/zones/{zone_id}/locations"
        )
        return data if isinstance(data, list) else []

    async def update_zone_locations(
        self, zone_id: int, locations: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        data = await self._request_json(
            "PUT",
            f"/wp-json/wc/v3/shipping/zones/{zone_id}/locations",
            json=locations,
        )
        return data if isinstance(data, list) else []

    async def list_zone_methods(self, zone_id: int) -> list[dict[str, Any]]:
        data = await self._get_json(
            f"/wp-json/wc/v3/shipping/zones/{zone_id}/methods"
        )
        return data if isinstance(data, list) else []

    async def get_zone_method(
        self, zone_id: int, instance_id: int
    ) -> dict[str, Any]:
        data = await self._get_json(
            f"/wp-json/wc/v3/shipping/zones/{zone_id}/methods/{instance_id}"
        )
        return data if isinstance(data, dict) else {}

    async def add_zone_method(
        self, zone_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        data = await self._request_json(
            "POST",
            f"/wp-json/wc/v3/shipping/zones/{zone_id}/methods",
            json=payload,
        )
        return data if isinstance(data, dict) else {}

    async def update_zone_method(
        self, zone_id: int, instance_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        data = await self._request_json(
            "PUT",
            f"/wp-json/wc/v3/shipping/zones/{zone_id}/methods/{instance_id}",
            json=payload,
        )
        return data if isinstance(data, dict) else {}

    async def delete_zone_method(self, zone_id: int, instance_id: int) -> None:
        url = (
            f"{self.base_url}/wp-json/wc/v3/shipping/zones/{zone_id}"
            f"/methods/{instance_id}"
        )
        try:
            response = await self._http.request(
                "DELETE",
                url,
                headers=self._auth_headers,
                allow_private=self._allow_private,
            )
        except httpx.HTTPError as exc:
            raise WooConnectionError(
                "Could not reach WooCommerce during method delete.",
                details={"url": url, "error": exc.__class__.__name__},
            ) from exc
        self._raise_for_status(response, url)

    async def list_available_methods(self) -> list[dict[str, Any]]:
        data = await self._get_json("/wp-json/wc/v3/shipping_methods")
        return data if isinstance(data, list) else []

    # --- Internals ---------------------------------------------------------

    async def _get_json(
        self, path: str, *, params: dict[str, Any] | None = None
    ) -> Any:
        url = f"{self.base_url}{path}"
        try:
            response = await self._http.request(
                "GET",
                url,
                headers=self._auth_headers,
                params=params,
                allow_private=self._allow_private,
            )
        except httpx.HTTPError as exc:
            raise WooConnectionError(
                "Could not reach WooCommerce.",
                details={"url": url, "error": exc.__class__.__name__},
            ) from exc

        self._raise_for_status(response, url)
        try:
            return response.json()
        except ValueError as exc:
            raise WooResponseError(
                "WooCommerce returned a non-JSON response.",
                details={"url": url, "status": response.status_code},
            ) from exc

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        try:
            response = await self._http.request(
                method,
                url,
                headers=self._auth_headers,
                json=json,
                allow_private=self._allow_private,
            )
        except httpx.HTTPError as exc:
            raise WooConnectionError(
                "Could not reach WooCommerce.",
                details={"url": url, "error": exc.__class__.__name__},
            ) from exc

        self._raise_for_status(response, url)
        try:
            return response.json()
        except ValueError as exc:
            raise WooResponseError(
                "WooCommerce returned a non-JSON response.",
                details={"url": url, "status": response.status_code},
            ) from exc

    @staticmethod
    def _raise_for_status(response: httpx.Response, url: str) -> None:
        if response.status_code in (200, 201, 202, 204):
            return
        if response.status_code in (401, 403):
            raise WooAuthError(
                "WooCommerce authentication failed.",
                details={"url": url, "status": response.status_code},
            )
        if response.status_code == 404:
            raise WooNotFoundError(
                "WooCommerce endpoint not found.",
                details={"url": url, "status": response.status_code},
            )
        detail: dict[str, Any] = {"url": url, "status": response.status_code}
        try:
            body = response.json()
            if isinstance(body, dict):
                if "code" in body:
                    detail["wc_code"] = body["code"]
                if "message" in body:
                    detail["wc_message"] = body["message"]
        except Exception:  # noqa: BLE001
            pass
        raise WooResponseError(
            "WooCommerce rejected the request.",
            details=detail,
        )