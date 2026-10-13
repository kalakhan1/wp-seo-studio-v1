"""API schema tests for /api/v1/backup."""

from __future__ import annotations

from httpx import AsyncClient


async def test_export_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/backup/export")
    assert response.status_code == 200
    body = response.json()
    assert "bundle" in body
    assert body["bundle"]["format"] == "wp-seo-studio.backup.v1"
    assert isinstance(body["warnings"], list)


async def test_import_dry_run_no_changes(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/backup/import",
        json={
            "bundle": {
                "format": "wp-seo-studio.backup.v1",
                "created_at": "2026-01-01T00:00:00Z",
                "app_version": "0.1.0",
                "connections": [
                    {
                        "label": "prod",
                        "base_url": "https://example.test",
                        "username": "admin",
                    }
                ],
                "prompt_templates": [],
                "app_settings": [],
            },
            "dry_run": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["dry_run"] is True
    assert body["connections_created"] == 1
    assert body["connections_skipped"] == 0


async def test_import_rejects_blank_label(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/backup/import",
        json={
            "bundle": {
                "format": "wp-seo-studio.backup.v1",
                "created_at": "2026-01-01T00:00:00Z",
                "app_version": "0.1.0",
                "connections": [{"label": "", "base_url": "x"}],
                "prompt_templates": [],
                "app_settings": [],
            },
            "dry_run": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert any("label" in e.lower() for e in body["errors"])