"""Unit tests for WordPress media operations in WordPressClient."""

from __future__ import annotations

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
from tests.fixtures.wp_responses import (
    UNAUTHORIZED_JSON,
)

JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 200


def _settings() -> Settings:
    return Settings(
        app_env="development",
        app_mode="mock",
        log_level="warning",
        http_timeout=5,
        http_max_retries=0,
        http_max_response_bytes=5_000_000,
    )


def _wp_media_json(media_id: int = 501) -> dict[str, Any]:
    return {
        "id": media_id,
        "title": {"rendered": "product-photo.jpg"},
        "source_url": "https://example.test/wp-content/uploads/product-photo.jpg",
        "mime_type": "image/jpeg",
        "alt_text": "Product photo",
        "caption": {"rendered": "A product photo"},
        "description": {"rendered": "Description here"},
        "media_details": {"width": 800, "height": 600, "sizes": {}},
    }


async def _build_client(handler: Any) -> tuple[WordPressClient, SafeHttpClient]:
    transport = httpx.MockTransport(handler)
    http = SafeHttpClient(_settings(), transport=transport)
    client = WordPressClient(
        base_url="https://example.test",
        username="admin",
        app_password="app-pass",
        http=http,
    )
    return client, http


async def test_upload_media_sends_multipart_and_returns_media() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["content_type"] = request.headers.get("content-type", "")
        captured["authorization"] = request.headers.get("authorization", "")
        return httpx.Response(201, json=_wp_media_json())

    client, http = await _build_client(handler)
    try:
        media = await client.upload_media(
            filename="product-photo.jpg",
            content=JPEG_BYTES,
            mime_type="image/jpeg",
            title="Product photo",
            alt_text="Alt text",
        )
        assert media.id == 501
        assert media.source_url.endswith("product-photo.jpg")
        assert media.mime_type == "image/jpeg"
        assert media.width() == 800
        assert media.height() == 600
    finally:
        await http.aclose()

    assert captured["method"] == "POST"
    assert captured["path"] == "/wp-json/wp/v2/media"
    assert captured["content_type"].startswith("multipart/form-data")
    assert captured["authorization"].startswith("Basic ")


async def test_get_media() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_wp_media_json(777))

    client, http = await _build_client(handler)
    try:
        media = await client.get_media(777)
        assert media.id == 777
    finally:
        await http.aclose()


async def test_update_media_sends_json_payload() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = request.content.decode("utf-8")
        return httpx.Response(200, json=_wp_media_json())

    client, http = await _build_client(handler)
    try:
        media = await client.update_media(
            501,
            alt_text="New alt",
            title="New title",
        )
        assert media.id == 501
    finally:
        await http.aclose()

    assert captured["method"] == "POST"
    assert captured["path"] == "/wp-json/wp/v2/media/501"
    assert "New alt" in captured["body"]
    assert "New title" in captured["body"]


async def test_delete_media() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["force"] = request.url.params.get("force")
        return httpx.Response(200, json={"deleted": True})

    client, http = await _build_client(handler)
    try:
        await client.delete_media(501, force=False)
    finally:
        await http.aclose()

    assert captured["method"] == "DELETE"
    assert captured["path"] == "/wp-json/wp/v2/media/501"
    assert captured["force"] is None


async def test_delete_media_force() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["force"] = request.url.params.get("force")
        return httpx.Response(200, json={"deleted": True})

    client, http = await _build_client(handler)
    try:
        await client.delete_media(501, force=True)
    finally:
        await http.aclose()

    assert captured["force"] == "true"


async def test_upload_media_auth_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json=UNAUTHORIZED_JSON)

    client, http = await _build_client(handler)
    try:
        with pytest.raises(WPAuthError):
            await client.upload_media(
                filename="x.jpg",
                content=JPEG_BYTES,
                mime_type="image/jpeg",
            )
    finally:
        await http.aclose()


async def test_get_media_not_found() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"code": "rest_post_invalid_id"})

    client, http = await _build_client(handler)
    try:
        with pytest.raises(WPNotFoundError):
            await client.get_media(9999)
    finally:
        await http.aclose()


async def test_update_media_server_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    client, http = await _build_client(handler)
    try:
        with pytest.raises(WPResponseError):
            await client.update_media(501, alt_text="x")
    finally:
        await http.aclose()