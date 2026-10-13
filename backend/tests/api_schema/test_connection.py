"""API schema tests for /api/v1/connection.

These tests mock the SafeHttpClient by overriding the route handler's HTTP
layer via dependency patching. Simpler: we test schema validation by
hitting endpoints without valid upstreams and asserting error envelopes.
"""

from __future__ import annotations

from httpx import AsyncClient


async def test_list_connections_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/connection")
    assert response.status_code == 200
    body = response.json()
    assert body == {"connections": []}


async def test_test_connection_rejects_http_when_require_https_true(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/connection/test",
        json={
            "base_url": "http://example.com",
            "username": "admin",
            "wp_app_password": "abcd efgh",
            "require_https": True,
        },
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


async def test_test_connection_rejects_missing_base_url(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/connection/test",
        json={"username": "admin"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


async def test_get_connection_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/connection/9999")
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


async def test_delete_connection_not_found(client: AsyncClient) -> None:
    response = await client.delete("/api/v1/connection/9999")
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


async def test_save_rejects_blank_label(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/connection",
        json={
            "label": "",
            "base_url": "https://example.com",
            "username": "admin",
            "wp_app_password": "abcd efgh",
        },
    )
    assert response.status_code == 422


async def test_save_rejects_non_http_url(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/connection",
        json={
            "label": "prod",
            "base_url": "ftp://example.com",
            "username": "admin",
            "wp_app_password": "abcd efgh",
        },
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"