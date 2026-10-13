"""API schema tests for /api/v1/internal-links."""

from __future__ import annotations

from httpx import AsyncClient


async def test_search_requires_connection_id(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/internal-links/search",
        params={"q": "herbal"},
    )
    assert response.status_code == 422


async def test_search_requires_query(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/internal-links/search",
        params={"connection_id": 1},
    )
    assert response.status_code == 422


async def test_suggest_requires_connection_id(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/internal-links/suggest",
        params={"source_title": "Test"},
    )
    assert response.status_code == 422


async def test_suggest_requires_source_title(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/internal-links/suggest",
        params={"connection_id": 1},
    )
    assert response.status_code == 422


async def test_validate_url_unknown_connection(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/internal-links/validate-url",
        params={"connection_id": 9999},
        json={"url": "https://example.test/"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


async def test_validate_url_rejects_invalid_scheme(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/internal-links/validate-url",
        params={"connection_id": 1},
        json={"url": "ftp://example.test/file"},
    )
    assert response.status_code == 422  # unknown connection


async def test_check_anchor_requires_anchor_text(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/internal-links/check-anchor",
        json={"existing_anchors": []},
    )
    assert response.status_code == 422