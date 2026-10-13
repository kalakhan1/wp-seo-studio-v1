"""Unit tests for capability discovery."""

from __future__ import annotations

from typing import Any

import httpx

from app.config.constants import CapabilityStatus
from app.config.settings import Settings
from app.core.http_client import SafeHttpClient
from app.integrations.wordpress.capabilities import discover_capabilities
from app.integrations.wordpress.client import WordPressClient
from app.integrations.woocommerce.client import WooCommerceClient
from tests.fixtures.wp_responses import (
    COMPANION_SETTINGS_JSON,
    CURRENT_USER_JSON,
    CURRENT_USER_LOW_CAPS_JSON,
    MEDIA_LIST_JSON,
    NOT_FOUND_JSON,
    POST_TYPES_JSON,
    SITE_INFO_JSON,
    SITE_INFO_JSON_WITH_COMPANION,
    SITE_INFO_JSON_WITH_WC,
    TAXONOMIES_JSON,
    UNAUTHORIZED_JSON,
    WC_PAYMENT_GATEWAYS_JSON,
    WC_PRODUCTS_JSON,
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


def _handler_from_routes(routes: dict[str, tuple[int, Any]]) -> Any:
    def handler(request: httpx.Request) -> httpx.Response:
        match = routes.get(request.url.path)
        if match is None:
            return httpx.Response(404, json=NOT_FOUND_JSON)
        status, body = match
        return httpx.Response(status, json=body)

    return handler


async def _run_discovery(
    routes: dict[str, tuple[int, Any]],
    *,
    with_wc: bool = False,
) -> Any:
    transport = httpx.MockTransport(_handler_from_routes(routes))
    http = SafeHttpClient(_settings(), transport=transport)
    wp_client = WordPressClient(
        base_url="https://example.test",
        username="admin",
        app_password="app-pass",
        http=http,
    )
    wc_client = None
    if with_wc:
        wc_client = WooCommerceClient(
            base_url="https://example.test",
            consumer_key="ck",
            consumer_secret="cs",
            http=http,
        )
    try:
        report = await discover_capabilities(
            base_url="https://example.test",
            wp_client=wp_client,
            wc_client=wc_client,
            http=http,
            auth_headers={"Authorization": "Basic xxx"},
        )
    finally:
        await http.aclose()
    return report


def _find(report: Any, key: str) -> Any:
    for item in report.capabilities:
        if item.key == key:
            return item
    raise AssertionError(f"capability {key!r} not found")


# --- Happy path -------------------------------------------------------------


async def test_full_happy_path_all_supported() -> None:
    routes = {
        "/wp-json": (200, SITE_INFO_JSON),
        "/wp-json/wp/v2/users/me": (200, CURRENT_USER_JSON),
        "/wp-json/wp/v2/types": (200, POST_TYPES_JSON),
        "/wp-json/wp/v2/taxonomies": (200, TAXONOMIES_JSON),
        "/wp-json/wp/v2/media": (200, MEDIA_LIST_JSON),
    }
    report = await _run_discovery(routes)

    assert _find(report, "wp.read.site_info").status == CapabilityStatus.SUPPORTED.value
    assert _find(report, "wp.read.current_user").status == CapabilityStatus.SUPPORTED.value
    assert _find(report, "wp.read.post_types").status == CapabilityStatus.SUPPORTED.value
    assert _find(report, "wp.read.taxonomies").status == CapabilityStatus.SUPPORTED.value
    assert _find(report, "wp.read.media").status == CapabilityStatus.SUPPORTED.value
    assert _find(report, "wp.write.posts").status == CapabilityStatus.SUPPORTED.value
    assert _find(report, "wp.write.pages").status == CapabilityStatus.SUPPORTED.value
    assert _find(report, "wp.write.media").status == CapabilityStatus.SUPPORTED.value
    assert report.site_info is not None
    assert report.site_info.name == "Herbal Care Demo"
    assert report.current_user is not None
    assert report.current_user.id == 7


# --- Auth failure -----------------------------------------------------------


async def test_auth_failure_marks_current_user_requires_elevated() -> None:
    routes = {
        "/wp-json": (200, SITE_INFO_JSON),
        "/wp-json/wp/v2/users/me": (401, UNAUTHORIZED_JSON),
        "/wp-json/wp/v2/types": (200, POST_TYPES_JSON),
        "/wp-json/wp/v2/taxonomies": (200, TAXONOMIES_JSON),
        "/wp-json/wp/v2/media": (200, MEDIA_LIST_JSON),
    }
    report = await _run_discovery(routes)
    assert _find(report, "wp.read.current_user").status == CapabilityStatus.REQUIRES_ELEVATED.value
    # Writes become not_verified because user is unknown
    assert _find(report, "wp.write.posts").status == CapabilityStatus.NOT_VERIFIED.value
    assert any("authenticate" in w.lower() for w in report.warnings)


# --- Low capability user ----------------------------------------------------


async def test_low_capability_user_marks_writes_requires_elevated() -> None:
    routes = {
        "/wp-json": (200, SITE_INFO_JSON),
        "/wp-json/wp/v2/users/me": (200, CURRENT_USER_LOW_CAPS_JSON),
        "/wp-json/wp/v2/types": (200, POST_TYPES_JSON),
        "/wp-json/wp/v2/taxonomies": (200, TAXONOMIES_JSON),
        "/wp-json/wp/v2/media": (200, MEDIA_LIST_JSON),
    }
    report = await _run_discovery(routes)
    assert (
        _find(report, "wp.write.posts").status
        == CapabilityStatus.REQUIRES_ELEVATED.value
    )
    assert (
        _find(report, "wp.write.categories").status
        == CapabilityStatus.REQUIRES_ELEVATED.value
    )


# --- Missing endpoints ------------------------------------------------------


async def test_missing_post_types_marks_not_verified() -> None:
    routes = {
        "/wp-json": (200, SITE_INFO_JSON),
        "/wp-json/wp/v2/users/me": (200, CURRENT_USER_JSON),
        "/wp-json/wp/v2/taxonomies": (200, TAXONOMIES_JSON),
        "/wp-json/wp/v2/media": (200, MEDIA_LIST_JSON),
    }
    report = await _run_discovery(routes)
    assert _find(report, "wp.read.post_types").status == CapabilityStatus.NOT_VERIFIED.value


# --- WooCommerce ------------------------------------------------------------


async def test_wc_without_credentials_requires_manual_setup() -> None:
    routes = {
        "/wp-json": (200, SITE_INFO_JSON),
        "/wp-json/wp/v2/users/me": (200, CURRENT_USER_JSON),
        "/wp-json/wp/v2/types": (200, POST_TYPES_JSON),
        "/wp-json/wp/v2/taxonomies": (200, TAXONOMIES_JSON),
        "/wp-json/wp/v2/media": (200, MEDIA_LIST_JSON),
    }
    report = await _run_discovery(routes, with_wc=False)
    assert (
        _find(report, "wc.read.products").status
        == CapabilityStatus.REQUIRES_MANUAL_SETUP.value
    )


async def test_wc_with_credentials_supported() -> None:
    routes = {
        "/wp-json": (200, SITE_INFO_JSON_WITH_WC),
        "/wp-json/wp/v2/users/me": (200, CURRENT_USER_JSON),
        "/wp-json/wp/v2/types": (200, POST_TYPES_JSON),
        "/wp-json/wp/v2/taxonomies": (200, TAXONOMIES_JSON),
        "/wp-json/wp/v2/media": (200, MEDIA_LIST_JSON),
        "/wp-json/wc/v3/products": (200, WC_PRODUCTS_JSON),
        "/wp-json/wc/v3/payment_gateways": (200, WC_PAYMENT_GATEWAYS_JSON),
        "/wp-json/wc/v3/shipping/zones": (200, WC_SHIPPING_ZONES_JSON),
    }
    report = await _run_discovery(routes, with_wc=True)
    assert _find(report, "wc.read.products").status == CapabilityStatus.SUPPORTED.value
    assert (
        _find(report, "wc.read.payment_gateways").status
        == CapabilityStatus.SUPPORTED.value
    )
    assert (
        _find(report, "wc.read.shipping_zones").status
        == CapabilityStatus.SUPPORTED.value
    )


async def test_wc_not_installed_unsupported() -> None:
    routes = {
        "/wp-json": (200, SITE_INFO_JSON),
        "/wp-json/wp/v2/users/me": (200, CURRENT_USER_JSON),
        "/wp-json/wp/v2/types": (200, POST_TYPES_JSON),
        "/wp-json/wp/v2/taxonomies": (200, TAXONOMIES_JSON),
        "/wp-json/wp/v2/media": (200, MEDIA_LIST_JSON),
    }
    report = await _run_discovery(routes, with_wc=True)
    # Products endpoint 404 -> unsupported
    assert _find(report, "wc.read.products").status == CapabilityStatus.UNSUPPORTED.value


async def test_wc_auth_failure_requires_manual_setup() -> None:
    routes = {
        "/wp-json": (200, SITE_INFO_JSON_WITH_WC),
        "/wp-json/wp/v2/users/me": (200, CURRENT_USER_JSON),
        "/wp-json/wp/v2/types": (200, POST_TYPES_JSON),
        "/wp-json/wp/v2/taxonomies": (200, TAXONOMIES_JSON),
        "/wp-json/wp/v2/media": (200, MEDIA_LIST_JSON),
        "/wp-json/wc/v3/products": (401, UNAUTHORIZED_JSON),
        "/wp-json/wc/v3/payment_gateways": (401, UNAUTHORIZED_JSON),
        "/wp-json/wc/v3/shipping/zones": (401, UNAUTHORIZED_JSON),
    }
    report = await _run_discovery(routes, with_wc=True)
    assert (
        _find(report, "wc.read.products").status
        == CapabilityStatus.REQUIRES_MANUAL_SETUP.value
    )


# --- Rank Math --------------------------------------------------------------


async def test_rankmath_without_companion_requires_plugin() -> None:
    routes = {
        "/wp-json": (200, SITE_INFO_JSON),
        "/wp-json/wp/v2/users/me": (200, CURRENT_USER_JSON),
        "/wp-json/wp/v2/types": (200, POST_TYPES_JSON),
        "/wp-json/wp/v2/taxonomies": (200, TAXONOMIES_JSON),
        "/wp-json/wp/v2/media": (200, MEDIA_LIST_JSON),
    }
    report = await _run_discovery(routes)
    assert (
        _find(report, "rankmath.read.settings").status
        == CapabilityStatus.REQUIRES_PLUGIN.value
    )
    assert (
        _find(report, "rankmath.write.meta").status
        == CapabilityStatus.REQUIRES_PLUGIN.value
    )
    assert report.rankmath.companion_plugin_detected is False


async def test_rankmath_with_companion_supported() -> None:
    routes = {
        "/wp-json": (200, SITE_INFO_JSON_WITH_COMPANION),
        "/wp-json/wp/v2/users/me": (200, CURRENT_USER_JSON),
        "/wp-json/wp/v2/types": (200, POST_TYPES_JSON),
        "/wp-json/wp/v2/taxonomies": (200, TAXONOMIES_JSON),
        "/wp-json/wp/v2/media": (200, MEDIA_LIST_JSON),
        "/wp-json/wp-seo-control/v1/settings": (200, COMPANION_SETTINGS_JSON),
    }
    report = await _run_discovery(routes)
    assert report.rankmath.companion_plugin_detected is True
    assert report.rankmath.companion_settings_available is True
    assert (
        _find(report, "rankmath.read.settings").status
        == CapabilityStatus.SUPPORTED.value
    )


# --- Summary ----------------------------------------------------------------


async def test_summary_counts_match_capabilities() -> None:
    routes = {
        "/wp-json": (200, SITE_INFO_JSON),
        "/wp-json/wp/v2/users/me": (200, CURRENT_USER_JSON),
        "/wp-json/wp/v2/types": (200, POST_TYPES_JSON),
        "/wp-json/wp/v2/taxonomies": (200, TAXONOMIES_JSON),
        "/wp-json/wp/v2/media": (200, MEDIA_LIST_JSON),
    }
    report = await _run_discovery(routes)
    total_from_items = (
        report.summary.supported
        + report.summary.read_only
        + report.summary.requires_elevated
        + report.summary.requires_plugin
        + report.summary.requires_manual_setup
        + report.summary.not_verified
        + report.summary.unsupported
    )
    assert total_from_items == len(report.capabilities)