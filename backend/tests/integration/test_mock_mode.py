"""Integration tests for the mock WordPress client.

The mock client now returns the same typed models as the real client, so
these tests verify both the shape and the type contract.
"""

from __future__ import annotations

from app.integrations.wordpress.types import (
    PostType,
    SiteInfo,
    Taxonomy,
    WPUser,
)
from tests.mocks.mock_wordpress.client import MockWordPressClient


async def test_mock_returns_site_info(mock_wp_client: MockWordPressClient) -> None:
    info = await mock_wp_client.get_site_info()
    assert isinstance(info, SiteInfo)
    assert info.name == "Mock Site"
    assert info.url == "https://example.test"


async def test_mock_returns_current_user(mock_wp_client: MockWordPressClient) -> None:
    user = await mock_wp_client.get_current_user()
    assert isinstance(user, WPUser)
    assert user.id == 1
    assert "administrator" in user.roles


async def test_mock_lists_post_types(mock_wp_client: MockWordPressClient) -> None:
    types = await mock_wp_client.list_post_types()
    assert all(isinstance(t, PostType) for t in types)
    slugs = {t.slug for t in types}
    assert {"post", "page", "product"}.issubset(slugs)


async def test_mock_lists_taxonomies(mock_wp_client: MockWordPressClient) -> None:
    taxonomies = await mock_wp_client.list_taxonomies()
    assert all(isinstance(t, Taxonomy) for t in taxonomies)
    slugs = {t.slug for t in taxonomies}
    assert {"category", "product_cat"}.issubset(slugs)


async def test_mock_list_media_empty_by_default(mock_wp_client: MockWordPressClient) -> None:
    media = await mock_wp_client.list_media()
    assert media == []


async def test_mock_returns_copies_not_shared_state(mock_wp_client: MockWordPressClient) -> None:
    first = await mock_wp_client.get_site_info()
    first.name = "Mutated"
    second = await mock_wp_client.get_site_info()
    assert second.name == "Mock Site"


async def test_mock_reset_restores_defaults(mock_wp_client: MockWordPressClient) -> None:
    mock_wp_client.routes.post_types.clear()
    assert mock_wp_client.routes.post_types == []
    mock_wp_client.reset()
    assert len(mock_wp_client.routes.post_types) == 3