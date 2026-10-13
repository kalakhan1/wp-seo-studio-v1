"""Unit tests for app.integrations.wordpress.client.WordPressClient.

Uses httpx.MockTransport to intercept requests. No real network is used.
"""

from __future__ import annotations

import base64
from typing import Any

import httpx
import pytest

from app.config.settings import Settings
from app.core.http_client import SafeHttpClient
from app.integrations.wordpress.client import WordPressClient
from app.integrations.wordpress.exceptions import (
    WPAuthError,
    WPNotFoundError,
    WPResponseError,
)
from app.integrations.wordpress.types import PostType, SiteInfo, Taxonomy, WPUser
from tests.fixtures.wp_responses import (
    CURRENT_USER_JSON,
    MEDIA_LIST_JSON,
    NOT_FOUND_JSON,
    POST_TYPES_JSON,
    SITE_INFO_JSON,
    TAXONOMIES_JSON,
    UNAUTHORIZED_JSON,
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


def _route_by_path(
    routes: dict[str, tuple[int, Any]],
) -> Any:
    """Build a MockTransport handler that returns responses by request path."""

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        match = routes.get(path)
        if match is None:
            return httpx.Response(
                404,
                json={"code": "rest_no_route", "message": "Not found"},
            )
        status, body = match
        return httpx.Response(status, json=body)

    return handler


async def _build_client(
    handler: Any,
    *,
    username: str = "admin",
    password: str = "app-pass",
) -> tuple[WordPressClient, SafeHttpClient]:
    transport = httpx.MockTransport(handler)
    http = SafeHttpClient(_settings(), transport=transport)
    client = WordPressClient(
        base_url="https://example.test",
        username=username,
        app_password=password,
        http=http,
    )
    return client, http


# --- Success paths ----------------------------------------------------------


async def test_get_site_info_parses_response() -> None:
    routes = {"/wp-json": (200, SITE_INFO_JSON)}
    client, http = await _build_client(_route_by_path(routes))
    try:
        info = await client.get_site_info()
        assert isinstance(info, SiteInfo)
        assert info.name == "Herbal Care Demo"
        assert "wc/v3" in info.namespaces
    finally:
        await http.aclose()


async def test_get_current_user_parses_response() -> None:
    routes = {"/wp-json/wp/v2/users/me": (200, CURRENT_USER_JSON)}
    client, http = await _build_client(_route_by_path(routes))
    try:
        user = await client.get_current_user()
        assert isinstance(user, WPUser)
        assert user.id == 7
        assert "editor" in user.roles
    finally:
        await http.aclose()


async def test_list_post_types_parses_dict_response() -> None:
    routes = {"/wp-json/wp/v2/types": (200, POST_TYPES_JSON)}
    client, http = await _build_client(_route_by_path(routes))
    try:
        types = await client.list_post_types()
        assert all(isinstance(t, PostType) for t in types)
        slugs = {t.slug for t in types}
        assert {"post", "page", "product"}.issubset(slugs)
    finally:
        await http.aclose()


async def test_list_taxonomies_parses_dict_response() -> None:
    routes = {"/wp-json/wp/v2/taxonomies": (200, TAXONOMIES_JSON)}
    client, http = await _build_client(_route_by_path(routes))
    try:
        taxonomies = await client.list_taxonomies()
        assert all(isinstance(t, Taxonomy) for t in taxonomies)
        slugs = {t.slug for t in taxonomies}
        assert {"category", "product_cat"}.issubset(slugs)
    finally:
        await http.aclose()


async def test_list_media_parses_list_response() -> None:
    routes = {"/wp-json/wp/v2/media": (200, MEDIA_LIST_JSON)}
    client, http = await _build_client(_route_by_path(routes))
    try:
        media = await client.list_media(per_page=10)
        assert len(media) == 2
        assert media[0].id == 101
    finally:
        await http.aclose()


# --- Auth header propagation ------------------------------------------------


async def test_sends_basic_auth_header() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers.get("authorization", "")
        return httpx.Response(200, json=SITE_INFO_JSON)

    client, http = await _build_client(handler, username="admin", password="app pass")
    try:
        await client.get_site_info()
    finally:
        await http.aclose()

    expected = base64.b64encode(b"admin:app pass").decode("ascii")
    assert captured["authorization"] == f"Basic {expected}"


# --- Error mapping ----------------------------------------------------------


async def test_401_raises_auth_error() -> None:
    routes = {"/wp-json/wp/v2/users/me": (401, UNAUTHORIZED_JSON)}
    client, http = await _build_client(_route_by_path(routes))
    try:
        with pytest.raises(WPAuthError) as exc:
            await client.get_current_user()
        assert exc.value.details.get("status") == 401
    finally:
        await http.aclose()


async def test_403_raises_auth_error() -> None:
    routes = {"/wp-json/wp/v2/users/me": (403, UNAUTHORIZED_JSON)}
    client, http = await _build_client(_route_by_path(routes))
    try:
        with pytest.raises(WPAuthError):
            await client.get_current_user()
    finally:
        await http.aclose()


async def test_404_raises_not_found() -> None:
    routes = {"/wp-json/wp/v2/media": (404, NOT_FOUND_JSON)}
    client, http = await _build_client(_route_by_path(routes))
    try:
        with pytest.raises(WPNotFoundError):
            await client.list_media()
    finally:
        await http.aclose()


async def test_500_raises_response_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    client, http = await _build_client(handler)
    try:
        with pytest.raises(WPResponseError):
            await client.get_site_info()
    finally:
        await http.aclose()


async def test_invalid_json_raises_response_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not-json", headers={"content-type": "text/plain"})

    client, http = await _build_client(handler)
    try:
        with pytest.raises(WPResponseError):
            await client.get_site_info()
    finally:
        await http.aclose()


# --- Constructor guards -----------------------------------------------------


async def test_empty_base_url_raises() -> None:
    http = SafeHttpClient(_settings())
    try:
        with pytest.raises(WPAuthError):
            WordPressClient(
                base_url="",
                username="admin",
                app_password="pass",
                http=http,
            )
    finally:
        await http.aclose()