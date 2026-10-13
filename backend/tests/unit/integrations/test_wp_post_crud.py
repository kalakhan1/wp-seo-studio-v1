"""Unit tests for WordPress post/page CRUD operations."""

from __future__ import annotations

import json
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
from app.integrations.wordpress.types import (
    WPCategory,
    WPPost,
    WPTag,
)
from tests.fixtures.wp_responses import (
    BAD_REQUEST_JSON,
    CATEGORIES_JSON,
    FORBIDDEN_JSON,
    NOT_FOUND_JSON,
    PAGE_JSON,
    POST_JSON,
    TAGS_JSON,
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
    """Routes keyed by (method, path). Falls back to 404."""
    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        match = routes.get(key)
        if match is None:
            return httpx.Response(404, json=NOT_FOUND_JSON)
        status, body = match
        return httpx.Response(status, json=body)
    return handler


async def _build(handler: Any) -> tuple[WordPressClient, SafeHttpClient]:
    transport = httpx.MockTransport(handler)
    http = SafeHttpClient(_settings(), transport=transport)
    client = WordPressClient(
        base_url="https://example.test",
        username="admin",
        app_password="app-pass",
        http=http,
    )
    return client, http


# --- Categories / Tags ------------------------------------------------------


async def test_list_categories() -> None:
    routes = {
        ("GET", "/wp-json/wp/v2/categories"): (200, CATEGORIES_JSON),
    }
    client, http = await _build(_route_by_path_and_method(routes))
    try:
        cats = await client.list_categories()
        assert len(cats) == 2
        assert all(isinstance(c, WPCategory) for c in cats)
        slugs = {c.slug for c in cats}
        assert {"hair-care", "skin-care"}.issubset(slugs)
    finally:
        await http.aclose()


async def test_list_tags() -> None:
    routes = {
        ("GET", "/wp-json/wp/v2/tags"): (200, TAGS_JSON),
    }
    client, http = await _build(_route_by_path_and_method(routes))
    try:
        tags = await client.list_tags()
        assert len(tags) == 2
        assert all(isinstance(t, WPTag) for t in tags)
    finally:
        await http.aclose()


# --- Create ----------------------------------------------------------------


async def test_create_post_sends_payload() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path == "/wp-json/wp/v2/posts":
            captured["body"] = json.loads(request.content.decode("utf-8"))
            return httpx.Response(201, json=POST_JSON)
        return httpx.Response(404, json=NOT_FOUND_JSON)

    client, http = await _build(handler)
    try:
        post = await client.create_post(
            {
                "title": "Badam Benefits Guide",
                "content": "<p>Badam is a nutrient-dense nut.</p>",
                "excerpt": "A practical guide to badam.",
                "status": "draft",
                "slug": "badam-benefits-guide",
                "categories": [5],
                "tags": [10],
            }
        )
        assert isinstance(post, WPPost)
        assert post.id == 202
        assert post.raw_title() == "Badam Benefits Guide"
    finally:
        await http.aclose()

    body = captured["body"]
    assert body["title"] == "Badam Benefits Guide"
    assert body["status"] == "draft"
    assert body["categories"] == [5]


async def test_create_page() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path == "/wp-json/wp/v2/pages":
            return httpx.Response(201, json=PAGE_JSON)
        return httpx.Response(404, json=NOT_FOUND_JSON)

    client, http = await _build(handler)
    try:
        page = await client.create_post(
            {
                "title": "About Us",
                "content": "<p>We sell herbal products.</p>",
                "status": "publish",
            },
            post_type="pages",
        )
        assert page.id == 303
        assert page.type == "page"
    finally:
        await http.aclose()


# --- Update ----------------------------------------------------------------


async def test_update_post() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if (
            request.method == "POST"
            and request.url.path == "/wp-json/wp/v2/posts/202"
        ):
            captured["body"] = json.loads(request.content.decode("utf-8"))
            return httpx.Response(200, json=POST_JSON)
        return httpx.Response(404, json=NOT_FOUND_JSON)

    client, http = await _build(handler)
    try:
        post = await client.update_post(202, {"title": "New title"})
        assert post.id == 202
    finally:
        await http.aclose()

    assert captured["body"] == {"title": "New title"}


# --- Get -------------------------------------------------------------------


async def test_get_post() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/wp-json/wp/v2/posts/202":
            return httpx.Response(200, json=POST_JSON)
        return httpx.Response(404, json=NOT_FOUND_JSON)

    client, http = await _build(handler)
    try:
        post = await client.get_post(202)
        assert post.id == 202
        assert post.status == "draft"
    finally:
        await http.aclose()


# --- Delete ----------------------------------------------------------------


async def test_delete_post_no_force() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if (
            request.method == "DELETE"
            and request.url.path == "/wp-json/wp/v2/posts/202"
        ):
            captured["force"] = request.url.params.get("force")
            return httpx.Response(200, json={"deleted": True})
        return httpx.Response(404, json=NOT_FOUND_JSON)

    client, http = await _build(handler)
    try:
        await client.delete_post(202)
    finally:
        await http.aclose()

    assert captured["force"] is None


async def test_delete_post_force() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "DELETE":
            captured["force"] = request.url.params.get("force")
            return httpx.Response(200, json={"deleted": True})
        return httpx.Response(404, json=NOT_FOUND_JSON)

    client, http = await _build(handler)
    try:
        await client.delete_post(202, force=True)
    finally:
        await http.aclose()

    assert captured["force"] == "true"


# --- Error mapping ----------------------------------------------------------


async def test_create_post_auth_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json=FORBIDDEN_JSON)

    client, http = await _build(handler)
    try:
        with pytest.raises(WPAuthError):
            await client.create_post({"title": "x"})
    finally:
        await http.aclose()


async def test_update_post_not_found() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json=NOT_FOUND_JSON)

    client, http = await _build(handler)
    try:
        with pytest.raises(WPNotFoundError):
            await client.update_post(9999, {"title": "x"})
    finally:
        await http.aclose()


async def test_create_post_bad_request_includes_wp_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json=BAD_REQUEST_JSON)

    client, http = await _build(handler)
    try:
        with pytest.raises(WPResponseError) as exc:
            await client.create_post({"title": "x", "slug": "%%%"})
        assert exc.value.details.get("wp_code") == "rest_invalid_param"
    finally:
        await http.aclose()