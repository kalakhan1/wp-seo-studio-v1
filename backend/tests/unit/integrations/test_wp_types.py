"""Unit tests for WordPress REST API typed models."""

from __future__ import annotations

from app.integrations.wordpress.types import (
    PostType,
    SiteInfo,
    Taxonomy,
    WPCategory,
    WPMedia,
    WPPost,
    WPTag,
    WPUser,
)
from tests.fixtures.wp_responses import (
    CATEGORIES_JSON,
    CURRENT_USER_JSON,
    MEDIA_LIST_JSON,
    PAGE_JSON,
    POST_JSON,
    POST_TYPES_JSON,
    SITE_INFO_JSON,
    TAGS_JSON,
    TAXONOMIES_JSON,
)


class TestSiteInfo:
    def test_parses_full_response(self) -> None:
        info = SiteInfo.model_validate(SITE_INFO_JSON)
        assert info.name == "Herbal Care Demo"
        assert info.url == "https://example.test"
        assert info.timezone_string == "Asia/Karachi"
        assert "wc/v3" in info.namespaces

    def test_ignores_unknown_fields(self) -> None:
        info = SiteInfo.model_validate(SITE_INFO_JSON)
        assert not hasattr(info, "site_logo")

    def test_defaults_when_empty(self) -> None:
        info = SiteInfo.model_validate({})
        assert info.name == ""
        assert info.namespaces == []


class TestPostType:
    def test_parses_from_dict(self) -> None:
        pt = PostType.model_validate(POST_TYPES_JSON["product"])
        assert pt.slug == "product"
        assert pt.rest_base == "product"
        assert pt.rest_namespace == "wc/v3"
        assert pt.hierarchical is False

    def test_supports_list(self) -> None:
        pt = PostType.model_validate(POST_TYPES_JSON["post"])
        assert "title" in pt.supports
        assert "thumbnail" in pt.supports


class TestTaxonomy:
    def test_parses_hierarchical(self) -> None:
        t = Taxonomy.model_validate(TAXONOMIES_JSON["category"])
        assert t.slug == "category"
        assert t.hierarchical is True
        assert "post" in t.types


class TestWPUser:
    def test_parses_roles_and_capabilities(self) -> None:
        user = WPUser.model_validate(CURRENT_USER_JSON)
        assert user.id == 7
        assert user.name == "Content Editor"
        assert "editor" in user.roles
        assert user.capabilities.get("publish_posts") is True


class TestWPMedia:
    def test_parses_image_with_details(self) -> None:
        media = WPMedia.model_validate(MEDIA_LIST_JSON[0])
        assert media.id == 101
        assert media.mime_type == "image/jpeg"
        assert media.media_details["width"] == 1200
        assert "woocommerce_thumbnail" in media.media_details["sizes"]
        assert media.width() == 1200
        assert media.height() == 1200

    def test_parses_minimal_media(self) -> None:
        media = WPMedia.model_validate(MEDIA_LIST_JSON[1])
        assert media.id == 102
        assert media.media_details["width"] == 800


class TestWPCategory:
    def test_parses_category(self) -> None:
        cat = WPCategory.model_validate(CATEGORIES_JSON[0])
        assert cat.id == 5
        assert cat.slug == "hair-care"
        assert cat.parent == 0
        assert cat.count == 12


class TestWPTag:
    def test_parses_tag(self) -> None:
        tag = WPTag.model_validate(TAGS_JSON[0])
        assert tag.id == 10
        assert tag.slug == "herbal"
        assert tag.count == 20


class TestWPPost:
    def test_parses_post(self) -> None:
        post = WPPost.model_validate(POST_JSON)
        assert post.id == 202
        assert post.type == "post"
        assert post.status == "draft"
        assert post.rendered_title() == "Badam Benefits Guide"
        assert post.raw_title() == "Badam Benefits Guide"
        assert "Badam" in post.raw_content()
        assert post.categories == [5]
        assert post.tags == [10]

    def test_parses_page(self) -> None:
        page = WPPost.model_validate(PAGE_JSON)
        assert page.id == 303
        assert page.type == "page"
        assert page.status == "publish"
        assert page.raw_title() == "About Us"
        assert page.categories == []
        assert page.parent == 0

    def test_rendered_vs_raw_fallback(self) -> None:
        data = {
            "id": 1,
            "title": {"rendered": "Rendered only"},
            "content": {"rendered": "<p>Rendered</p>"},
        }
        post = WPPost.model_validate(data)
        assert post.raw_title() == "Rendered only"
        assert post.raw_content() == "<p>Rendered</p>"