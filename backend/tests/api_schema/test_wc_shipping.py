"""API schema tests for /api/v1/wc/shipping."""

from __future__ import annotations

from httpx import AsyncClient


async def test_list_zones_requires_connection_id(client: AsyncClient) -> None:
    response = await client.get("/api/v1/wc/shipping/zones")
    assert response.status_code == 422


async def test_create_zone_requires_connection_id(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/wc/shipping/zones",
        json={"name": "Pakistan"},
    )
    assert response.status_code == 422


async def test_create_zone_rejects_blank_name(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/wc/shipping/zones",
        params={"connection_id": 1},
        json={"name": ""},
    )
    assert response.status_code == 422


async def test_get_zone_requires_connection_id(client: AsyncClient) -> None:
    response = await client.get("/api/v1/wc/shipping/zones/1")
    assert response.status_code == 422


async def test_update_locations_rejects_invalid_type(client: AsyncClient) -> None:
    response = await client.put(
        "/api/v1/wc/shipping/zones/1/locations",
        params={"connection_id": 1},
        json={"locations": [{"code": "PK", "type": "invalid"}]},
    )
    assert response.status_code == 422


async def test_add_method_requires_method_id(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/wc/shipping/zones/1/methods",
        params={"connection_id": 1},
        json={"enabled": True},
    )
    assert response.status_code == 422


async def test_list_available_methods_requires_connection_id(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/wc/shipping/methods")
    assert response.status_code == 422