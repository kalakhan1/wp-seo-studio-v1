"""API schema tests for /api/v1/wc/gateways."""

from __future__ import annotations

from httpx import AsyncClient


async def test_list_gateways_requires_connection_id(client: AsyncClient) -> None:
    response = await client.get("/api/v1/wc/gateways")
    assert response.status_code == 422


async def test_get_cod_requires_connection_id(client: AsyncClient) -> None:
    response = await client.get("/api/v1/wc/gateways/cod")
    assert response.status_code == 422


async def test_update_cod_requires_connection_id(client: AsyncClient) -> None:
    response = await client.put(
        "/api/v1/wc/gateways/cod",
        json={"enabled": True},
    )
    assert response.status_code == 422


async def test_update_cod_unknown_connection(client: AsyncClient) -> None:
    response = await client.put(
        "/api/v1/wc/gateways/cod",
        params={"connection_id": 9999},
        json={"enabled": True},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


async def test_update_cod_rejects_unknown_field(client: AsyncClient) -> None:
    response = await client.put(
        "/api/v1/wc/gateways/cod",
        params={"connection_id": 1},
        json={"random_field": "x"},
    )
    assert response.status_code == 422


async def test_get_gateway_requires_connection_id(client: AsyncClient) -> None:
    response = await client.get("/api/v1/wc/gateways/bacs")
    assert response.status_code == 422