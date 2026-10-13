"""Unit tests for RankMathClient using httpx.MockTransport."""

from __future__ import annotations

import base64
from typing import Any

import httpx
import pytest

from app.config.settings import Settings
from app.core.http_client import SafeHttpClient
from app.integrations.rankmath.client import RankMathClient
from app.integrations.rankmath.exceptions import (
    RankMathCompanionMissingError,
    RankMathInactiveError,
    RankMathMetaError,
)
from app.integrations.rankmath.types import RankMathMeta


def _settings() -> Settings:
    return Settings(
        app_env="development",
        app_mode="mock",
        log_level="warning",
        http_timeout=5,
        http_max_retries=0,
        http_max_response_bytes=5_000_000,
    )


def _auth_headers() -> dict[str, str]:
    token = base64.b64encode(b"admin:pass").decode("ascii")
    return {"Authorization": f"Basic {token}"}


def _route_by_path(routes: dict[str, tuple[int, Any]]) -> Any:
    def handler(request: httpx.Request) -> httpx.Response:
        match = routes.get(request.url.path)
        if match is None:
            return httpx.Response(404, json={"code": "rest_no_route"})
        status, body = match
        return httpx.Response(status, json=body)

    return handler


async def _build(
    handler: Any,
) -> tuple[RankMathClient, SafeHttpClient]:
    transport = httpx.MockTransport(handler)
    http = SafeHttpClient(_settings(), transport=transport)
    client = RankMathClient(
        base_url="https://example.test",
        auth_headers=_auth_headers(),
        http=http,
    )
    return client, http


# --- Status ----------------------------------------------------------------


async def test_get_status_returns_info() -> None:
    routes = {
        "/wp-json/wp-seo-control/v1/status": (
            200,
            {
                "ok": True,
                "plugin_version": "0.1.0",
                "rank_math_active": True,
                "namespace": "wp-seo-control/v1",
            },
        )
    }
    client, http = await _build(_route_by_path(routes))
    try:
        status = await client.get_status()
        assert status["ok"] is True
        assert status["rank_math_active"] is True
    finally:
        await http.aclose()


async def test_get_status_missing_plugin_raises() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"code": "rest_no_route"})

    client, http = await _build(handler)
    try:
        with pytest.raises(RankMathCompanionMissingError):
            await client.get_status()
    finally:
        await http.aclose()


# --- Get meta ---------------------------------------------------------------


async def test_get_meta_returns_typed_model() -> None:
    routes = {
        "/wp-json/wp-seo-control/v1/rankmath/meta/42": (
            200,
            {
                "ok": True,
                "post_id": 42,
                "meta": {
                    "title": "Herbal Hair Oil",
                    "description": "Natural oil for daily care.",
                    "focus_keyword": "herbal hair oil",
                    "robots": ["index", "follow"],
                    "unknown_field": "must be ignored",
                },
            },
        )
    }
    client, http = await _build(_route_by_path(routes))
    try:
        meta = await client.get_meta(42)
        assert isinstance(meta, RankMathMeta)
        assert meta.title == "Herbal Hair Oil"
        assert meta.description == "Natural oil for daily care."
        assert meta.focus_keyword == "herbal hair oil"
        assert meta.robots == ["index", "follow"]
    finally:
        await http.aclose()


async def test_get_meta_missing_companion_raises() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"code": "rest_no_route"})

    client, http = await _build(handler)
    try:
        with pytest.raises(RankMathCompanionMissingError):
            await client.get_meta(1)
    finally:
        await http.aclose()


async def test_get_meta_rankmath_inactive_raises() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(409, json={"code": "wpseo_rankmath_inactive"})

    client, http = await _build(handler)
    try:
        with pytest.raises(RankMathInactiveError):
            await client.get_meta(1)
    finally:
        await http.aclose()


async def test_get_meta_auth_failure_raises() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"code": "wpseo_forbidden"})

    client, http = await _build(handler)
    try:
        with pytest.raises(RankMathMetaError):
            await client.get_meta(1)
    finally:
        await http.aclose()


# --- Set meta ---------------------------------------------------------------


async def test_set_meta_sends_only_provided_fields() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.content.decode("utf-8")
        return httpx.Response(
            200,
            json={
                "ok": True,
                "post_id": 42,
                "meta": {
                    "title": "New title",
                    "focus_keyword": "new keyword",
                },
            },
        )

    client, http = await _build(handler)
    try:
        meta = RankMathMeta(title="New title", focus_keyword="new keyword")
        result = await client.set_meta(42, meta)
        assert result.title == "New title"
        assert result.focus_keyword == "new keyword"
    finally:
        await http.aclose()

    body = captured["body"]
    assert "New title" in body
    assert "new keyword" in body
    assert "description" not in body
    assert "facebook_title" not in body


async def test_set_meta_sends_robots_as_array() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.content.decode("utf-8")
        return httpx.Response(
            200,
            json={
                "ok": True,
                "post_id": 42,
                "meta": {"robots": ["index", "follow"]},
            },
        )

    client, http = await _build(handler)
    try:
        await client.set_meta(42, RankMathMeta(robots=["index", "follow"]))
    finally:
        await http.aclose()

    body = captured["body"]
    assert '"robots": ["index", "follow"]' in body or '"robots":["index","follow"]' in body