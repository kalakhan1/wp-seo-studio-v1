"""End-to-end smoke test: boot app, call health and settings, verify responses."""

from __future__ import annotations

from httpx import AsyncClient


async def test_root_endpoint(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"]
    assert data["version"] == "0.1.0"
    assert data["health"].endswith("/health")


async def test_full_smoke_flow(client: AsyncClient) -> None:
    # 1. Health is ok
    health = (await client.get("/api/v1/health")).json()
    assert health["status"] == "ok"
    assert health["mode"] == "mock"

    # 2. Read settings
    settings = (await client.get("/api/v1/app-settings")).json()
    assert settings["app_mode"] == "mock"

    # 3. Change log level
    updated = (await client.put("/api/v1/app-settings", json={"log_level": "debug"})).json()
    assert updated["log_level"] == "debug"

    # 4. Health still ok
    health2 = (await client.get("/api/v1/health")).json()
    assert health2["status"] == "ok"


async def test_404_returns_error_envelope(client: AsyncClient) -> None:
    response = await client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert "error" in body
    assert body["error"]["code"].startswith("HTTP_")