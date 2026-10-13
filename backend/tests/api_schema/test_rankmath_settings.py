"""API schema tests for /api/v1/rankmath/settings."""

from __future__ import annotations

from httpx import AsyncClient


async def test_status_requires_connection_id(client: AsyncClient) -> None:
    response = await client.get("/api/v1/rankmath/settings/status")
    assert response.status_code == 422


async def test_get_settings_requires_connection_id(client: AsyncClient) -> None:
    response = await client.get("/api/v1/rankmath/settings")
    assert response.status_code == 422


async def test_update_settings_requires_connection_id(client: AsyncClient) -> None:
    response = await client.put(
        "/api/v1/rankmath/settings",
        json={"title_separator": "|"},
    )
    assert response.status_code == 422


async def test_update_settings_rejects_unknown_field(
    client: AsyncClient,
) -> None:
    response = await client.put(
        "/api/v1/rankmath/settings",
        params={"connection_id": 1},
        json={"not_a_real_field": "x"},
    )
    assert response.status_code == 422


async def test_update_settings_unknown_connection(client: AsyncClient) -> None:
    response = await client.put(
        "/api/v1/rankmath/settings",
        params={"connection_id": 9999},
        json={"title_separator": "|"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] in ("VALIDATION_ERROR", "RANKMATH_COMPANION_MISSING")