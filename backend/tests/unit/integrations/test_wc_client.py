"""Unit tests for app.integrations.woocommerce.client.WooCommerceClient.

Uses httpx.MockTransport. No real network.
"""

from __future__ import annotations

import base64
from typing import Any

import httpx
import pytest

from app.config.settings import Settings
from app.core.http_client import SafeHttpClient
from app.integrations.woocommerce.client import WooCommerceClient
from app.integrations.woocommerce.exceptions import (
    WooAuthError,
    WooNotFoundError,
    WooResponseError,
)
from app.integrations.woocommerce.types import WCProduct
from tests.fixtures.wc_responses import (
    WC_PRODUCT_LIST_JSON,
)
from tests.fixtures.wp_responses import (
    NOT_FOUND_JSON,
    UNAUTHORIZED_JSON,
    WC_PAYMENT_GATEWAYS_JSON,
    WC_SHIPPING_ZONES_JSON,
)


def _settings() -> Settings:
    return Settings(
        app_env="development",
        app_mode="mock",
        log_level="warning",
        http_timeout=5,
        http_max_retries=0,
        http_max_response_bytes=5_000_000,
    )


def _route_by_path(routes: dict[str, tuple[int, Any]]) -> Any:
    def handler(request: httpx.Request) -> httpx.Response:
        match = routes.get(request.url.path)
        if match is None:
            return httpx.Response(404, json=NOT_FOUND_JSON)
        status, body = match
        return httpx.Response(status, json=body)

    return handler


async def _build_client(handler: Any) -> tuple[WooCommerceClient, SafeHttpClient]:
    transport = httpx.MockTransport(handler)
    http = SafeHttpClient(_settings(), transport=transport)
    client = WooCommerceClient(
        base_url="https://example.test",
        consumer_key="ck_abc123",
        consumer_secret="cs_xyz789",
        http=http,
    )
    return client, http


async def test_sends_basic_auth_header() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers.get("authorization", "")
        return httpx.Response(200, json=WC_PRODUCT_LIST_JSON)

    client, http = await _build_client(handler)
    try:
        await client.list_products()
    finally:
        await http.aclose()

    expected = base64.b64encode(b"ck_abc123:cs_xyz789").decode("ascii")
    assert captured["authorization"] == f"Basic {expected}"


async def test_list_products_parses_response() -> None:
    routes = {"/wp-json/wc/v3/products": (200, WC_PRODUCT_LIST_JSON)}
    client, http = await _build_client(_route_by_path(routes))
    try:
        products = await client.list_products()
        assert len(products) == 2
        # Now returns typed WCProduct models
        assert all(isinstance(p, WCProduct) for p in products)
        assert products[0].name == "Herbal Hair Oil"
        assert products[0].slug == "herbal-hair-oil"
    finally:
        await http.aclose()


async def test_list_payment_gateways_parses_response() -> None:
    routes = {
        "/wp-json/wc/v3/payment_gateways": (200, WC_PAYMENT_GATEWAYS_JSON),
    }
    client, http = await _build_client(_route_by_path(routes))
    try:
        gateways = await client.list_payment_gateways()
        ids = {g["id"] for g in gateways}
        assert "cod" in ids
    finally:
        await http.aclose()


async def test_list_shipping_zones_parses_response() -> None:
    routes = {
        "/wp-json/wc/v3/shipping/zones": (200, WC_SHIPPING_ZONES_JSON),
    }
    client, http = await _build_client(_route_by_path(routes))
    try:
        zones = await client.list_shipping_zones()
        assert zones[0]["name"] == "Pakistan"
    finally:
        await http.aclose()


async def test_ping_returns_true_on_success() -> None:
    routes = {"/wp-json/wc/v3/products": (200, WC_PRODUCT_LIST_JSON)}
    client, http = await _build_client(_route_by_path(routes))
    try:
        assert await client.ping() is True
    finally:
        await http.aclose()


async def test_ping_returns_false_on_404() -> None:
    client, http = await _build_client(
        lambda _: httpx.Response(404, json=NOT_FOUND_JSON)
    )
    try:
        assert await client.ping() is False
    finally:
        await http.aclose()


async def test_ping_returns_false_on_401() -> None:
    client, http = await _build_client(
        lambda _: httpx.Response(401, json=UNAUTHORIZED_JSON)
    )
    try:
        assert await client.ping() is False
    finally:
        await http.aclose()


async def test_401_raises_auth_error() -> None:
    routes = {"/wp-json/wc/v3/products": (401, UNAUTHORIZED_JSON)}
    client, http = await _build_client(_route_by_path(routes))
    try:
        with pytest.raises(WooAuthError):
            await client.list_products()
    finally:
        await http.aclose()


async def test_404_raises_not_found() -> None:
    routes = {
        "/wp-json/wc/v3/payment_gateways": (404, NOT_FOUND_JSON),
    }
    client, http = await _build_client(_route_by_path(routes))
    try:
        with pytest.raises(WooNotFoundError):
            await client.list_payment_gateways()
    finally:
        await http.aclose()


async def test_500_raises_response_error() -> None:
    client, http = await _build_client(
        lambda _: httpx.Response(500, json={"error": "boom"})
    )
    try:
        with pytest.raises(WooResponseError):
            await client.list_products()
    finally:
        await http.aclose()


async def test_empty_credentials_raise() -> None:
    http = SafeHttpClient(_settings())
    try:
        with pytest.raises(WooAuthError):
            WooCommerceClient(
                base_url="https://example.test",
                consumer_key="",
                consumer_secret="",
                http=http,
            )
    finally:
        await http.aclose()