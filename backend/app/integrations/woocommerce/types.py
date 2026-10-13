"""Typed data models for WooCommerce REST API responses.

Only the fields the application uses are typed. Unknown fields are
ignored on parsing.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WCImage(BaseModel):
    """Product image reference. Either `id` (existing media) or `src` is used."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    src: str | None = None
    name: str | None = None
    alt: str | None = None


class WCCategory(BaseModel):
    """Product category from /wp-json/wc/v3/products/categories."""

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str = ""
    slug: str = ""
    parent: int = 0
    description: str = ""
    count: int = 0
    image: dict[str, Any] | None = None


class WCTag(BaseModel):
    """Product tag from /wp-json/wc/v3/products/tags."""

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str = ""
    slug: str = ""
    count: int = 0


class WCProduct(BaseModel):
    """Product from /wp-json/wc/v3/products.

    Price fields come back as strings (WooCommerce API convention). All
    numeric fields may be empty strings when unset.
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str = ""
    slug: str = ""
    type: str = "simple"
    status: str = "draft"

    permalink: str = ""
    sku: str = ""

    description: str = ""
    short_description: str = ""

    regular_price: str = ""
    sale_price: str = ""
    price: str = ""
    date_on_sale_from: str | None = None
    date_on_sale_to: str | None = None

    tax_status: str = "taxable"
    tax_class: str = ""

    manage_stock: bool = False
    stock_quantity: int | None = None
    stock_status: str = "instock"
    backorders: str = "no"
    low_stock_amount: int | None = None
    sold_individually: bool = False

    weight: str = ""
    dimensions: dict[str, str] = Field(default_factory=dict)
    shipping_class: str = ""

    featured: bool = False
    catalog_visibility: str = "visible"
    on_sale: bool = False
    total_sales: int = 0
    average_rating: str = "0"
    rating_count: int = 0

    reviews_allowed: bool = True
    purchase_note: str = ""

    categories: list[dict[str, Any]] = Field(default_factory=list)
    tags: list[dict[str, Any]] = Field(default_factory=list)
    images: list[WCImage] = Field(default_factory=list)
    attributes: list[dict[str, Any]] = Field(default_factory=list)
    meta_data: list[dict[str, Any]] = Field(default_factory=list)

    related_ids: list[int] = Field(default_factory=list)
    upsell_ids: list[int] = Field(default_factory=list)
    cross_sell_ids: list[int] = Field(default_factory=list)

    menu_order: int = 0
    parent_id: int = 0

    # --- Helpers -----------------------------------------------------------

    def category_ids(self) -> list[int]:
        out: list[int] = []
        for c in self.categories:
            cid = c.get("id") if isinstance(c, dict) else None
            if isinstance(cid, int):
                out.append(cid)
        return out

    def tag_ids(self) -> list[int]:
        out: list[int] = []
        for t in self.tags:
            tid = t.get("id") if isinstance(t, dict) else None
            if isinstance(tid, int):
                out.append(tid)
        return out

    def feature_image_id(self) -> int | None:
        if not self.images:
            return None
        first = self.images[0]
        return first.id