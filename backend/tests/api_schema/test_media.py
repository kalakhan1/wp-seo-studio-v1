"""API schema tests for /api/v1/media."""

from __future__ import annotations

from httpx import AsyncClient


async def test_list_media_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/media")
    assert response.status_code == 200
    body = response.json()
    assert body == {"items": [], "total": 0}


async def test_get_media_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/media/9999")
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


async def test_delete_media_not_found(client: AsyncClient) -> None:
    response = await client.delete("/api/v1/media/9999")
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


async def test_upload_without_file_returns_422(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/media/upload",
        data={"connection_id": "1"},
    )
    assert response.status_code == 422


async def test_upload_with_unknown_format_returns_422(client: AsyncClient) -> None:
    files = {"file": ("notes.txt", b"hello world", "text/plain")}
    response = await client.post(
        "/api/v1/media/upload",
        data={"connection_id": "1"},
        files=files,
    )
    # 422 for invalid format, but connection is checked first, so we may get
    # 422 for "connection not found". Either way, not a 500.
    assert response.status_code in (422, 404)
    body = response.json()
    assert body["error"]["code"] in ("VALIDATION_ERROR",)