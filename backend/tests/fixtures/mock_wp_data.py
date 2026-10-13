"""Deterministic sample data for tests.

Keep values stable. Tests that reference these strings rely on exact matches.
"""

from __future__ import annotations

from typing import Any


SAMPLE_SITE_INFO: dict[str, Any] = {
    "name": "Herbal Care Demo",
    "description": "Natural herbal products for daily care",
    "url": "https://example.test",
    "home": "https://example.test",
    "timezone_string": "UTC",
}


SAMPLE_POST_TYPES: list[dict[str, Any]] = [
    {
        "slug": "post",
        "name": "Posts",
        "rest_base": "posts",
        "rest_namespace": "wp/v2",
    },
    {
        "slug": "page",
        "name": "Pages",
        "rest_base": "pages",
        "rest_namespace": "wp/v2",
    },
    {
        "slug": "product",
        "name": "Products",
        "rest_base": "product",
        "rest_namespace": "wc/v3",
    },
]


SAMPLE_PRODUCT: dict[str, Any] = {
    "id": 101,
    "name": "Herbal Hair Oil",
    "slug": "herbal-hair-oil",
    "type": "simple",
    "status": "draft",
    "regular_price": "499.00",
    "sale_price": "",
    "sku": "HHO-001",
    "description": "Natural herbal hair oil for daily care.",
    "short_description": "Daily care hair oil.",
    "categories": [{"id": 5, "name": "Hair Care", "slug": "hair-care"}],
    "images": [],
    "permalink": "https://example.test/product/herbal-hair-oil/",
}


SAMPLE_POST: dict[str, Any] = {
    "id": 202,
    "title": {"rendered": "Badam Benefits Guide"},
    "slug": "badam-benefits-guide",
    "status": "draft",
    "excerpt": {"rendered": "A practical guide to badam."},
    "content": {"rendered": "<p>Badam is a nutrient-dense nut.</p>"},
    "link": "https://example.test/badam-benefits-guide/",
}


SAMPLE_MEDIA: dict[str, Any] = {
    "id": 303,
    "title": {"rendered": "herbal-hair-oil.jpg"},
    "source_url": "https://example.test/wp-content/uploads/herbal-hair-oil.jpg",
    "mime_type": "image/jpeg",
    "media_details": {
        "width": 1200,
        "height": 1200,
        "sizes": {
            "thumbnail": {"width": 150, "height": 150},
            "medium": {"width": 300, "height": 300},
            "large": {"width": 1024, "height": 1024},
            "woocommerce_thumbnail": {"width": 300, "height": 300},
            "woocommerce_single": {"width": 600, "height": 600},
        },
    },
}