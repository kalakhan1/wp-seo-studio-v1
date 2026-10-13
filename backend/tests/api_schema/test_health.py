"""Schema and behaviour tests for GET /api/v1/health."""

from __future__ import annotations

from httpx import AsyncClient


async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in {"ok", "degraded", "failed"}
    assert data["mode"] == "mock"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data

    components = data["components"]
    names = {c["name"] for c in components}
    assert {"settings", "mode", "database"}.issubset(names)


async def test_health_includes_request_id_header(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert "x-request-id" in {k.lower() for k in response.headers.keys()}


async def test_health_echoes_incoming_request_id(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/health",
        headers={"X-Request-ID": "abc123"},
    )
    assert response.headers.get("X-Request-ID") == "abc123"