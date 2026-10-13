"""API schema tests for /api/v1/ai-prompts."""

from __future__ import annotations

from httpx import AsyncClient


async def test_status_returns_mock_by_default(client: AsyncClient) -> None:
    response = await client.get("/api/v1/ai-prompts/status")
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] in ("mock", "none")
    assert body["available"] is True


async def test_list_templates_seeds_defaults(client: AsyncClient) -> None:
    response = await client.get("/api/v1/ai-prompts/templates")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) >= 2
    types = {t["template_type"] for t in body["items"]}
    assert {"product", "blog"}.issubset(types)


async def test_get_product_template(client: AsyncClient) -> None:
    response = await client.get("/api/v1/ai-prompts/templates/product")
    assert response.status_code == 200
    body = response.json()
    assert body["template_type"] == "product"
    assert "NEEDS_INPUT" in body["content"]


async def test_get_unknown_template(client: AsyncClient) -> None:
    response = await client.get("/api/v1/ai-prompts/templates/unknown")
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


async def test_update_template(client: AsyncClient) -> None:
    # Get existing template first
    g = await client.get("/api/v1/ai-prompts/templates/blog")
    assert g.status_code == 200

    response = await client.put(
        "/api/v1/ai-prompts/templates/blog",
        json={"content": "Custom content for test"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["content"] == "Custom content for test"
    assert body["is_default"] is False


async def test_restore_template(client: AsyncClient) -> None:
    # Modify first
    await client.put(
        "/api/v1/ai-prompts/templates/blog",
        json={"content": "Temporary content"},
    )
    # Restore
    response = await client.post(
        "/api/v1/ai-prompts/templates/blog/restore",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["restored"] is True
    assert body["template"]["is_default"] is True
    assert "blog article" in body["template"]["content"].lower()


async def test_generate_returns_mock_parsed(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/ai-prompts/generate",
        json={"prompt": "Write something", "template_type": "product"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["provider"] == "mock"
    assert body["parsed"] is not None
    assert isinstance(body["parsed"], dict)


async def test_generate_rejects_empty_prompt(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/ai-prompts/generate",
        json={"prompt": ""},
    )
    assert response.status_code == 422