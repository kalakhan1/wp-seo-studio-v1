"""Unit tests for WooCommerce settings client methods."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from app.config.settings import Settings
from app.core.http_client import SafeHttpClient
from app.integrations.woocommerce.client import WooCommerceClient
from tests.fixtures.wc_responses import (
    WC_SETTINGS_GENERAL_JSON,
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


async def test_get_settings_group() -> None:
    routes = {
        ("GET", "/wp-json/wc/v3/settings/general"): (200, WC_SETTINGS_GENERAL_JSON),
    }
    client, http = await _build(_route_by_path_and_method(routes))
    try:
        result = await client.get_settings_group("general")
        assert isinstance(result, list)
        assert any(r["id"] == "woocommerce_currency" for r in result)
    finally:
        await http.aclose()


async def test_get_setting() -> None:
    routes = {
        ("GET", "/wp-json/wc/v3/settings/general/woocommerce_currency"): (
            200,
            {
                "id": "woocommerce_currency",
                "type": "select",
                "value": "PKR",
                "label": "Currency",
            },
        ),
    }
    client, http = await _build(_route_by_path_and_method(routes))
    try:
        result = await client.get_setting("general", "woocommerce_currency")
        assert result["value"] == "PKR"
    finally:
        await http.aclose()


async def test_update_setting_sends_wrapped_value() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "PUT":
            captured["body"] = json.loads(request.content.decode("utf-8"))
            return httpx.Response(
                200,
                json={
                    "id": "woocommerce_currency",
                    "type": "select",
                    "value": "USD",
                },
            )
        return httpx.Response(404, json={"code": "not_found"})

    client, http = await _build(handler)
    try:
        result = await client.update_setting(
            "general", "woocommerce_currency", "USD"
        )
        assert result["value"] == "USD"
    finally:
        await http.aclose()

    assert captured["body"] == {"value": "USD"}


async def test_update_setting_array_value() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            200,
            json={
                "id": "woocommerce_specific_allowed_countries",
                "type": "multiselect",
                "value": ["PK", "US"],
            },
        )

    client, http = await _build(handler)
    try:
        result = await client.update_setting(
            "general", "woocommerce_specific_allowed_countries", ["PK", "US"]
        )
        assert result["value"] == ["PK", "US"]
    finally:
        await http.aclose()

    assert captured["body"] == {"value": ["PK", "US"]}