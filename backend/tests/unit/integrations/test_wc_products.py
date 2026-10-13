"""Unit tests for WooCommerce product operations."""

from __future__ import annotations

import json
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
from app.integrations.woocommerce.types import (
    WCCategory,
    WCProduct,
    WCTag,
)
from tests.fixtures.wc_responses import (
    WC_DUPLICATE_SKU_ERROR_JSON,
    WC_PRODUCT_CATEGORIES_JSON,
    WC_PRODUCT_JSON,
    WC_PRODUCT_LIST_JSON,
    WC_PRODUCT_MINIMAL_JSON,
    WC_PRODUCT_TAGS_JSON,
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


def _route_by_path_and_method(
    routes: dict[tuple[str, str], tuple[int, Any]],
) -> Any:
    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        match = routes.get(key)
        if match is None:
            return httpx.Response(404, json={"code": "not_found"})
        status, body = match
        return httpx.Response(status, json=body)

    return handler


async def _build(handler: Any) -> tuple[WooCommerceClient, SafeHttpClient]:
    transport = httpx.MockTransport(handler)
    http = SafeHttpClient(_settings(), transport=transport)
    client = WooCommerceClient(
        base_url="https://example.test",
        consumer_key="ck_abc",
        consumer_secret="cs_xyz",
        http=http,
    )
    return client, http


# --- Read -------------------------------------------------------------------


async def test_list_products() -> None:
    routes = {
        ("GET", "/wp-json/wc/v3/products"): (200, WC_PRODUCT_LIST_JSON),
    }
    client, http = await _build(_route_by_path_and_method(routes))
    try:
        products = await client.list_products()
        assert len(products) == 2
        assert all(isinstance(p, WCProduct) for p in products)
        assert products[0].name == "Herbal Hair Oil"
        assert products[0].category_ids() == [5]
        assert products[0].tag_ids() == [10]
        assert products[0].feature_image_id() == 101
    finally:
        await http.aclose()


async def test_get_product() -> None:
    routes = {
        ("GET", "/wp-json/wc/v3/products/501"): (200, WC_PRODUCT_JSON),
    }
    client, http = await _build(_route_by_path_and_method(routes))
    try:
        product = await client.get_product(501)
        assert product.id == 501
        assert product.sku == "HHO-001"
        assert product.regular_price == "499.00"
    finally:
        await http.aclose()


# --- Create -----------------------------------------------------------------


async def test_create_product_sends_payload() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path == "/wp-json/wc/v3/products":
            captured["body"] = json.loads(request.content.decode("utf-8"))
            return httpx.Response(201, json=WC_PRODUCT_JSON)
        return httpx.Response(404, json={"code": "not_found"})

    client, http = await _build(handler)
    try:
        product = await client.create_product(
            {
                "name": "Herbal Hair Oil",
                "type": "simple",
                "status": "draft",
                "regular_price": "499.00",
                "sku": "HHO-001",
                "categories": [{"id": 5}],
                "tags": [{"id": 10}],
                "images": [{"id": 101, "alt": "Product"}],
            }
        )
        assert product.id == 501
    finally:
        await http.aclose()

    body = captured["body"]
    assert body["name"] == "Herbal Hair Oil"
    assert body["regular_price"] == "499.00"
    assert body["categories"] == [{"id": 5}]


async def test_create_product_duplicate_sku() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json=WC_DUPLICATE_SKU_ERROR_JSON)

    client, http = await _build(handler)
    try:
        with pytest.raises(WooResponseError) as exc:
            await client.create_product({"name": "X", "sku": "DUP"})
        assert exc.value.details.get("wc_code") == "product_invalid_sku"
    finally:
        await http.aclose()


# --- Update -----------------------------------------------------------------


async def test_update_product() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if (
            request.method == "PUT"
            and request.url.path == "/wp-json/wc/v3/products/501"
        ):
            captured["body"] = json.loads(request.content.decode("utf-8"))
            return httpx.Response(200, json=WC_PRODUCT_MINIMAL_JSON)
        return httpx.Response(404, json={"code": "not_found"})

    client, http = await _build(handler)
    try:
        product = await client.update_product(501, {"regular_price": "199.00"})
        assert product.id == 502
    finally:
        await http.aclose()

    assert captured["body"] == {"regular_price": "199.00"}


# --- Delete -----------------------------------------------------------------


async def test_delete_product_no_force() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "DELETE":
            captured["force"] = request.url.params.get("force")
            return httpx.Response(200, json={"deleted": True})
        return httpx.Response(404, json={"code": "not_found"})

    client, http = await _build(handler)
    try:
        await client.delete_product(501)
    finally:
        await http.aclose()

    assert captured["force"] is None


async def test_delete_product_force() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "DELETE":
            captured["force"] = request.url.params.get("force")
            return httpx.Response(200, json={"deleted": True})
        return httpx.Response(404, json={"code": "not_found"})

    client, http = await _build(handler)
    try:
        await client.delete_product(501, force=True)
    finally:
        await http.aclose()

    assert captured["force"] == "true"


# --- Taxonomies -------------------------------------------------------------


async def test_list_product_categories() -> None:
    routes = {
        ("GET", "/wp-json/wc/v3/products/categories"): (200, WC_PRODUCT_CATEGORIES_JSON),
    }
    client, http = await _build(_route_by_path_and_method(routes))
    try:
        cats = await client.list_product_categories()
        assert len(cats) == 2
        assert all(isinstance(c, WCCategory) for c in cats)
        assert cats[0].name == "Hair Care"
    finally:
        await http.aclose()


async def test_list_product_tags() -> None:
    routes = {
        ("GET", "/wp-json/wc/v3/products/tags"): (200, WC_PRODUCT_TAGS_JSON),
    }
    client, http = await _build(_route_by_path_and_method(routes))
    try:
        tags = await client.list_product_tags()
        assert len(tags) == 2
        assert all(isinstance(t, WCTag) for t in tags)
    finally:
        await http.aclose()


# --- Error mapping ----------------------------------------------------------


async def test_create_product_auth_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"code": "woocommerce_rest_cannot_create"})

    client, http = await _build(handler)
    try:
        with pytest.raises(WooAuthError):
            await client.create_product({"name": "X"})
    finally:
        await http.aclose()


async def test_get_product_not_found() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"code": "woocommerce_rest_shop_product_invalid_id"})

    client, http = await _build(handler)
    try:
        with pytest.raises(WooNotFoundError):
            await client.get_product(9999)
    finally:
        await http.aclose()