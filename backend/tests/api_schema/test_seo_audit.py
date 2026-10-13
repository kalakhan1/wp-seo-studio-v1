"""API schema tests for /api/v1/seo-audit."""

from __future__ import annotations

from httpx import AsyncClient


async def test_run_requires_connection_id(client: AsyncClient) -> None:
    response = await client.post("/api/v1/seo-audit/run")
    assert response.status_code == 422


async def test_run_unknown_connection(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/seo-audit/run",
        params={"connection_id": 9999},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


async def test_history_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/seo-audit/history")
    assert response.status_code == 200
    body = response.json()
    assert body == {"items": []}


async def test_history_with_limit(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/seo-audit/history",
        params={"limit": 5},
    )
    assert response.status_code == 200