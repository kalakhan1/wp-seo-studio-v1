"""API schema tests for /api/v1/queue."""

from __future__ import annotations

from httpx import AsyncClient


async def test_list_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/queue")
    assert response.status_code == 200
    body = response.json()
    assert body == {"items": [], "total": 0}


async def test_summary_zero(client: AsyncClient) -> None:
    response = await client.get("/api/v1/queue/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["pending"] == 0
    assert body["success"] == 0


async def test_get_job_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/queue/9999")
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


async def test_cancel_job_not_found(client: AsyncClient) -> None:
    response = await client.post("/api/v1/queue/9999/cancel")
    assert response.status_code == 422


async def test_retry_job_not_found(client: AsyncClient) -> None:
    response = await client.post("/api/v1/queue/9999/retry")
    assert response.status_code == 422