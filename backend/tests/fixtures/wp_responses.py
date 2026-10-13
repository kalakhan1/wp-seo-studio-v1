"""Sample WordPress REST API JSON responses for tests."""

from __future__ import annotations

from typing import Any

# --- WordPress core ---------------------------------------------------------

SITE_INFO_JSON: dict[str, Any] = {
    "name": "Herbal Care Demo",
    "description": "Natural herbal products for daily care",
    "url": "https://example.test",
    "home": "https://example.test",
    "gmt_offset": 5.0,
    "timezone_string": "Asia/Karachi",
    "namespaces": ["wp/v2", "wp-site-health/v1", "wc/v3"],
    "site_logo": 123,
}

SITE_INFO_JSON_WITH_WC: dict[str, Any] = {
    **SITE_INFO_JSON,
    "namespaces": ["wp/v2", "wp-site-health/v1", "wc/v3"],
}

SITE_INFO_JSON_WITH_COMPANION: dict[str, Any] = {
    **SITE_INFO_JSON_WITH_WC,
    "namespaces": [
        "wp/v2",
        "wp-site-health/v1",
        "wc/v3",
        "wp-seo-control/v1",
    ],
}

CURRENT_USER_JSON: dict[str, Any] = {
    "id": 7,
    "name": "Content Editor",
    "slug": "content-editor",
    "roles": ["editor"],
    "capabilities": {
        "edit_posts": True,
        "publish_posts": True,
        "edit_pages": True,
        "publish_pages": True,
        "upload_files": True,
        "manage_categories": True,
        "manage_options": False,
    },
}

CURRENT_USER_LOW_CAPS_JSON: dict[str, Any] = {
    "id": 9,
    "name": "Contributor",
    "slug": "contributor",
    "roles": ["contributor"],
    "capabilities": {
        "edit_posts": True,
        "publish_posts": False,
        "upload_files": True,
        "manage_categories": False,
    },
}

POST_TYPES_JSON: dict[str, Any] = {
    "post": {
        "slug": "post",
        "name": "Posts",
        "rest_base": "posts",
        "rest_namespace": "wp/v2",
        "hierarchical": False,
        "supports": ["title", "editor", "excerpt", "thumbnail"],
    },
    "page": {
        "slug": "page",
        "name": "Pages",
        "rest_base": "pages",
        "rest_namespace": "wp/v2",
        "hierarchical": True,
        "supports": ["title", "editor", "excerpt", "thumbnail"],
    },
    "product": {
        "slug": "product",
        "name": "Products",
        "rest_base": "product",
        "rest_namespace": "wc/v3",
        "hierarchical": False,
        "supports": ["title", "editor", "excerpt", "thumbnail"],
    },
}

TAXONOMIES_JSON: dict[str, Any] = {
    "category": {
        "slug": "category",
        "name": "Categories",
        "rest_base": "categories",
        "rest_namespace": "wp/v2",
        "hierarchical": True,
        "types": ["post"],
    },
    "post_tag": {
        "slug": "post_tag",
        "name": "Tags",
        "rest_base": "tags",
        "rest_namespace": "wp/v2",
        "hierarchical": False,
        "types": ["post"],
    },
    "product_cat": {
        "slug": "product_cat",
        "name": "Product Categories",
        "rest_base": "products/categories",
        "rest_namespace": "wc/v3",
        "hierarchical": True,
        "types": ["product"],
    },
}

CATEGORIES_JSON: list[dict[str, Any]] = [
    {
        "id": 5,
        "name": "Hair Care",
        "slug": "hair-care",
        "description": "",
        "parent": 0,
        "count": 12,
    },
    {
        "id": 6,
        "name": "Skin Care",
        "slug": "skin-care",
        "description": "",
        "parent": 0,
        "count": 8,
    },
]

TAGS_JSON: list[dict[str, Any]] = [
    {
        "id": 10,
        "name": "herbal",
        "slug": "herbal",
        "description": "",
        "count": 20,
    },
    {
        "id": 11,
        "name": "natural",
        "slug": "natural",
        "description": "",
        "count": 15,
    },
]

POST_JSON: dict[str, Any] = {
    "id": 202,
    "type": "post",
    "status": "draft",
    "slug": "badam-benefits-guide",
    "link": "https://example.test/badam-benefits-guide/",
    "title": {"rendered": "Badam Benefits Guide", "raw": "Badam Benefits Guide"},
    "content": {
        "rendered": "<p>Badam is a nutrient-dense nut.</p>",
        "raw": "<p>Badam is a nutrient-dense nut.</p>",
    },
    "excerpt": {
        "rendered": "A practical guide to badam.",
        "raw": "A practical guide to badam.",
    },
    "author": 7,
    "featured_media": 0,
    "parent": 0,
    "menu_order": 0,
    "comment_status": "open",
    "ping_status": "open",
    "categories": [5],
    "tags": [10],
    "date": "2026-10-12T10:00:00",
    "date_gmt": "2026-10-12T05:00:00",
    "modified": "2026-10-12T10:00:00",
    "modified_gmt": "2026-10-12T05:00:00",
}

PAGE_JSON: dict[str, Any] = {
    "id": 303,
    "type": "page",
    "status": "publish",
    "slug": "about-us",
    "link": "https://example.test/about-us/",
    "title": {"rendered": "About Us", "raw": "About Us"},
    "content": {
        "rendered": "<p>We sell herbal products.</p>",
        "raw": "<p>We sell herbal products.</p>",
    },
    "excerpt": {"rendered": "", "raw": ""},
    "author": 7,
    "featured_media": 0,
    "parent": 0,
    "menu_order": 0,
    "comment_status": "closed",
    "ping_status": "closed",
    "categories": [],
    "tags": [],
    "date": "2026-10-12T10:00:00",
    "date_gmt": "2026-10-12T05:00:00",
    "modified": "2026-10-12T10:00:00",
    "modified_gmt": "2026-10-12T05:00:00",
}

MEDIA_LIST_JSON: list[dict[str, Any]] = [
    {
        "id": 101,
        "title": {"rendered": "herbal-hair-oil.jpg"},
        "source_url": "https://example.test/wp-content/uploads/herbal-hair-oil.jpg",
        "mime_type": "image/jpeg",
        "media_details": {
            "width": 1200,
            "height": 1200,
            "sizes": {
                "thumbnail": {"width": 150, "height": 150},
                "medium": {"width": 300, "height": 300},
                "woocommerce_thumbnail": {"width": 300, "height": 300},
            },
        },
    },
    {
        "id": 102,
        "title": {"rendered": "badam.jpg"},
        "source_url": "https://example.test/wp-content/uploads/badam.jpg",
        "mime_type": "image/jpeg",
        "media_details": {"width": 800, "height": 600, "sizes": {}},
    },
]

UNAUTHORIZED_JSON: dict[str, Any] = {
    "code": "rest_cannot_access",
    "message": "Sorry, you are not allowed to do that.",
    "data": {"status": 401},
}

FORBIDDEN_JSON: dict[str, Any] = {
    "code": "rest_cannot_edit",
    "message": "Sorry, you are not allowed to edit this post.",
    "data": {"status": 403},
}

NOT_FOUND_JSON: dict[str, Any] = {
    "code": "rest_no_route",
    "message": "No route was found matching the URL and request method.",
    "data": {"status": 404},
}

BAD_REQUEST_JSON: dict[str, Any] = {
    "code": "rest_invalid_param",
    "message": "Invalid parameter(s): slug",
    "data": {"status": 400},
}

# --- WooCommerce (legacy shapes used by some tests) ------------------------

WC_PRODUCTS_JSON: list[dict[str, Any]] = [
    {
        "id": 501,
        "name": "Herbal Hair Oil",
        "slug": "herbal-hair-oil",
        "status": "publish",
        "type": "simple",
        "price": "499.00",
    }
]

WC_PAYMENT_GATEWAYS_JSON: list[dict[str, Any]] = [
    {
        "id": "cod",
        "title": "Cash on delivery",
        "enabled": True,
        "method_title": "Cash on delivery",
        "method_description": "Pay with cash upon delivery.",
    },
    {
        "id": "bacs",
        "title": "Direct bank transfer",
        "enabled": False,
    },
]

WC_SHIPPING_ZONES_JSON: list[dict[str, Any]] = [
    {
        "id": 1,
        "name": "Pakistan",
        "order": 0,
    }
]

WC_SETTINGS_GENERAL_JSON: list[dict[str, Any]] = [
    {
        "id": "woocommerce_store_address",
        "label": "Address",
        "value": "",
        "type": "text",
    }
]

# --- Companion plugin -------------------------------------------------------

COMPANION_SETTINGS_JSON: dict[str, Any] = {
    "ok": True,
    "plugin_version": "0.1.0",
    "rank_math_active": True,
}

COMPANION_META_JSON: dict[str, Any] = {
    "ok": True,
    "post_id": 202,
    "meta": {
        "title": "Badam Benefits Guide",
        "description": "A practical guide to badam.",
        "focus_keyword": "badam benefits",
        "robots": ["index", "follow"],
    },
}