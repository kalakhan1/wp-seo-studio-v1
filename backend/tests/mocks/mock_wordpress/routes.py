"""Canned data for the mock WordPress client.

Uses the real typed models (SiteInfo, PostType, Taxonomy, WPUser, WPMedia)
so the mock mirrors the production client's return types exactly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.integrations.wordpress.types import (
    PostType,
    SiteInfo,
    Taxonomy,
    WPMedia,
    WPUser,
)


def _default_site_info() -> SiteInfo:
    return SiteInfo(
        name="Mock Site",
        description="In-memory WordPress for development",
        url="https://example.test",
        home="https://example.test",
        gmt_offset=0.0,
        timezone_string="UTC",
        namespaces=["wp/v2", "wp-site-health/v1", "wc/v3"],
    )


def _default_post_types() -> list[PostType]:
    return [
        PostType(
            slug="post",
            name="Posts",
            rest_base="posts",
            rest_namespace="wp/v2",
            hierarchical=False,
            supports=["title", "editor", "excerpt", "thumbnail"],
        ),
        PostType(
            slug="page",
            name="Pages",
            rest_base="pages",
            rest_namespace="wp/v2",
            hierarchical=True,
            supports=["title", "editor", "excerpt", "thumbnail"],
        ),
        PostType(
            slug="product",
            name="Products",
            rest_base="product",
            rest_namespace="wc/v3",
            hierarchical=False,
            supports=["title", "editor", "excerpt", "thumbnail"],
        ),
    ]


def _default_taxonomies() -> list[Taxonomy]:
    return [
        Taxonomy(
            slug="category",
            name="Categories",
            rest_base="categories",
            rest_namespace="wp/v2",
            hierarchical=True,
            types=["post"],
        ),
        Taxonomy(
            slug="post_tag",
            name="Tags",
            rest_base="tags",
            rest_namespace="wp/v2",
            hierarchical=False,
            types=["post"],
        ),
        Taxonomy(
            slug="product_cat",
            name="Product Categories",
            rest_base="products/categories",
            rest_namespace="wc/v3",
            hierarchical=True,
            types=["product"],
        ),
    ]


def _default_current_user() -> WPUser:
    return WPUser(
        id=1,
        name="Demo Admin",
        slug="demo-admin",
        roles=["administrator"],
        capabilities={
            "edit_posts": True,
            "publish_posts": True,
            "upload_files": True,
            "manage_options": True,
        },
    )


@dataclass
class MockWordPressRoutes:
    """Canned data for the mock client."""

    site_info: SiteInfo = field(default_factory=_default_site_info)
    post_types: list[PostType] = field(default_factory=_default_post_types)
    taxonomies: list[Taxonomy] = field(default_factory=_default_taxonomies)
    current_user: WPUser = field(default_factory=_default_current_user)
    media: list[WPMedia] = field(default_factory=list)