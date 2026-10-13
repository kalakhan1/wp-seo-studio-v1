"""API schema tests for /api/v1/history."""

from __future__ import annotations

from httpx import AsyncClient


async def test_list_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/history")
    assert response.status_code == 200
    body = response.json()
    assert body == {"items": [], "total": 0}


async def test_summary_zero(client: AsyncClient) -> None:
    response = await client.get("/api/v1/history/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0