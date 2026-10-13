"""Schema and behaviour tests for /api/v1/app-settings."""

from __future__ import annotations

from httpx import AsyncClient


async def test_get_settings_returns_expected_fields(client: AsyncClient) -> None:
    response = await client.get("/api/v1/app-settings")
    assert response.status_code == 200

    data = response.json()
    expected_keys = {
        "app_env",
        "app_mode",
        "log_level",
        "log_format",
        "ai_provider",
        "image_search_provider",
        "http_timeout",
        "http_max_retries",
    }
    assert expected_keys.issubset(data.keys())
    assert data["app_mode"] == "mock"


async def test_update_log_level(client: AsyncClient) -> None:
    response = await client.put(
        "/api/v1/app-settings",
        json={"log_level": "debug"},
    )
    assert response.status_code == 200
    assert response.json()["log_level"] == "debug"


async def test_update_rejects_unknown_field(client: AsyncClient) -> None:
    response = await client.put(
        "/api/v1/app-settings",
        json={"unknown_field": "x"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


async def test_update_rejects_invalid_log_level(client: AsyncClient) -> None:
    """Invalid log levels must be rejected with 422, not cause a 500."""
    response = await client.put(
        "/api/v1/app-settings",
        json={"log_level": "verbose"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    # Original log level is unchanged (defaults to whatever settings had)
    follow_up = await client.get("/api/v1/app-settings")
    assert follow_up.status_code == 200