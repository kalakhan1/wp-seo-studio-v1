"""API schema tests for /api/v1/products."""

from __future__ import annotations

from httpx import AsyncClient


async def test_create_product_requires_connection_id(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/products",
        json={"name": "Herbal Hair Oil"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


async def test_create_product_rejects_blank_name(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/products",
        json={"connection_id": 1, "name": ""},
    )
    assert response.status_code == 422


async def test_create_product_unknown_connection(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/products",
        json={"connection_id": 9999, "name": "Herbal Hair Oil"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


async def test_get_product_missing_connection_id(client: AsyncClient) -> None:
    response = await client.get("/api/v1/products/501")
    assert response.status_code == 422


async def test_list_products_missing_connection_id(client: AsyncClient) -> None:
    response = await client.get("/api/v1/products")
    assert response.status_code == 422


async def test_delete_product_missing_connection_id(client: AsyncClient) -> None:
    response = await client.delete("/api/v1/products/501")
    assert response.status_code == 422