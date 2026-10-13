"""Unit tests for app.core.http_client.SafeHttpClient.

These tests use a mocked transport so no real network is contacted.
"""

from __future__ import annotations

import httpx
import pytest

from app.config.settings import Settings
from app.core.exceptions import AppError, SSRFBlockedError, WPError
from app.core.http_client import SafeHttpClient


def _settings(**overrides: object) -> Settings:
    defaults: dict[str, object] = {
        "app_env": "development",
        "app_mode": "mock",
        "log_level": "warning",
        "http_timeout": 5,
        "http_max_retries": 1,
        "http_max_response_bytes": 1_000_000,
    }
    defaults.update(overrides)
    return Settings(**defaults)  # type: ignore[arg-type]


async def test_blocks_private_ip() -> None:
    async with SafeHttpClient(_settings()) as client:
        with pytest.raises(SSRFBlockedError):
            await client.get("http://127.0.0.1/")


async def test_retries_on_5xx_then_succeeds() -> None:
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        if call_count["n"] < 2:
            return httpx.Response(503, json={"error": "temporary"})
        return httpx.Response(200, json={"ok": True})

    client = SafeHttpClient(_settings(http_max_retries=2))
    # Replace internal client with one that uses a mock transport
    await client.aclose()
    client._client = httpx.AsyncClient(  # noqa: SLF001
        transport=httpx.MockTransport(handler),
        timeout=5.0,
        follow_redirects=False,
    )
    try:
        response = await client.get("https://example.com/")
        assert response.status_code == 200
        assert call_count["n"] == 2
    finally:
        await client.aclose()


async def test_enforces_max_response_size() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"x" * 5000)

    client = SafeHttpClient(_settings(http_max_response_bytes=1024))
    await client.aclose()
    client._client = httpx.AsyncClient(  # noqa: SLF001
        transport=httpx.MockTransport(handler),
        timeout=5.0,
        follow_redirects=False,
    )
    try:
        with pytest.raises(AppError, match="maximum allowed size"):
            await client.get("https://example.com/")
    finally:
        await client.aclose()


async def test_transport_error_after_retries_raises_wp_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    client = SafeHttpClient(_settings(http_max_retries=1))
    await client.aclose()
    client._client = httpx.AsyncClient(  # noqa: SLF001
        transport=httpx.MockTransport(handler),
        timeout=5.0,
        follow_redirects=False,
    )
    try:
        with pytest.raises(WPError):
            await client.get("https://example.com/")
    finally:
        await client.aclose()