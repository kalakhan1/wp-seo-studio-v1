"""API schema tests for /api/v1/image-presets."""

from __future__ import annotations

from httpx import AsyncClient


async def test_list_presets(client: AsyncClient) -> None:
    response = await client.get("/api/v1/image-presets")
    assert response.status_code == 200
    body = response.json()

    assert "suggested" in body
    assert "css" in body
    assert len(body["suggested"]) >= 4
    assert len(body["css"]) >= 3

    keys = {p["key"] for p in body["suggested"]}
    assert "product_card" in keys
    assert "blog_featured" in keys

    css_keys = {p["key"] for p in body["css"]}
    assert "square_cover" in css_keys


async def test_discover_requires_connection_id(client: AsyncClient) -> None:
    response = await client.get("/api/v1/image-presets/discovered")
    assert response.status_code == 422


async def test_discover_unknown_connection(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/image-presets/discovered",
        params={"connection_id": 9999},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"