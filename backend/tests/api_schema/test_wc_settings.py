"""API schema tests for /api/v1/wc/settings."""

from __future__ import annotations

from httpx import AsyncClient


async def test_list_groups(client: AsyncClient) -> None:
    response = await client.get("/api/v1/wc/settings/groups")
    assert response.status_code == 200
    groups = response.json()
    assert isinstance(groups, list)
    assert "general" in groups
    assert "checkout" in groups


async def test_get_group_requires_connection_id(client: AsyncClient) -> None:
    response = await client.get("/api/v1/wc/settings/general")
    assert response.status_code == 422


async def test_get_group_unknown_connection(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/wc/settings/general",
        params={"connection_id": 9999},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


async def test_get_group_unknown_group(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/wc/settings/does-not-exist",
        params={"connection_id": 1},
    )
    # Group validation happens inside service; either 422 with our
    # validation error or 422 for unknown connection.
    assert response.status_code == 422


async def test_update_setting_requires_value(client: AsyncClient) -> None:
    response = await client.put(
        "/api/v1/wc/settings/checkout/woocommerce_enable_coupons",
        params={"connection_id": 1},
        json={},
    )
    assert response.status_code == 422


async def test_store_profile_requires_connection_id(client: AsyncClient) -> None:
    response = await client.get("/api/v1/wc/settings/store-profile")
    assert response.status_code == 422