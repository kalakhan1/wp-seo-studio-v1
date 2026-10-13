"""API schema tests for /api/v1/content."""

from __future__ import annotations

from httpx import AsyncClient


async def test_create_post_requires_connection_id(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/content/post",
        json={
            "kind": "post",
            "title": "Test",
        },
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


async def test_create_post_rejects_blank_title(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/content/post",
        json={
            "connection_id": 1,
            "kind": "post",
            "title": "",
        },
    )
    assert response.status_code == 422


async def test_create_post_schedule_without_date_fails(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/content/post",
        json={
            "connection_id": 1,
            "kind": "post",
            "title": "Test",
            "status": "future",
        },
    )
    assert response.status_code == 422


async def test_create_post_unknown_connection(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/content/post",
        json={
            "connection_id": 9999,
            "kind": "post",
            "title": "Test",
            "status": "draft",
        },
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


async def test_get_content_invalid_kind(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/content/foobar/1",
        params={"connection_id": 1},
    )
    assert response.status_code == 422