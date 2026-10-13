"""Schemas for WooCommerce product operations."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.integrations.rankmath.types import RankMathMeta


ProductStatus = Literal["draft", "pending", "private", "publish"]
ProductType = Literal["simple"]  # Phase 3 supports simple products only
CatalogVisibility = Literal["visible", "catalog", "search", "hidden"]
StockStatus = Literal["instock", "outofstock", "onbackorder"]
Backorders = Literal["no", "notify", "yes"]
TaxStatus = Literal["taxable", "shipping", "none"]


class ProductImageInput(BaseModel):
    """Image for a product. Either an existing media id or a source URL."""

    model_config = ConfigDict(extra="forbid")

    id: int | None = Field(default=None, ge=1)
    src: str | None = Field(default=None, max_length=2000)
    alt: str | None = Field(default=None, max_length=500)


class ProductDimensions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    length: str = Field(default="", max_length=20)
    width: str = Field(default="", max_length=20)
    height: str = Field(default="", max_length=20)


# --- Create -----------------------------------------------------------------


class ProductCreateRequest(BaseModel):
    """Create a WooCommerce product.

    Phase 3 supports simple products only. Variations, grouped products,
    and external products are deferred to a later phase.
    """

    model_config = ConfigDict(extra="forbid")

    connection_id: int = Field(..., ge=1)

    # Basic
    name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Product name.",
        examples=["Herbal Hair Oil"],
    )
    slug: str = Field(default="", max_length=300)
    type: ProductType = Field(default="simple")
    status: ProductStatus = Field(default="draft")
    featured: bool = False
    catalog_visibility: CatalogVisibility = "visible"

    description: str = Field(
        default="",
        description="Full product description (HTML allowed).",
    )
    short_description: str = Field(default="")

    sku: str = Field(
        default="",
        max_length=100,
        description="Unique SKU, if known.",
        examples=["HHO-001"],
    )

    # Pricing
    regular_price: str = Field(default="", max_length=20)
    sale_price: str = Field(default="", max_length=20)
    date_on_sale_from: str | None = None
    date_on_sale_to: str | None = None
    tax_status: TaxStatus = "taxable"
    tax_class: str = Field(default="", max_length=100)

    # Inventory
    manage_stock: bool = False
    stock_quantity: int | None = Field(default=None, ge=0)
    stock_status: StockStatus = "instock"
    backorders: Backorders = "no"
    low_stock_amount: int | None = Field(default=None, ge=0)
    sold_individually: bool = False

    # Shipping
    weight: str = Field(default="", max_length=20)
    dimensions: ProductDimensions = Field(default_factory=ProductDimensions)
    shipping_class: str = Field(default="", max_length=100)

    # Organization
    category_ids: list[int] = Field(default_factory=list)
    tag_ids: list[int] = Field(default_factory=list)

    # Media
    images: list[ProductImageInput] = Field(default_factory=list)

    # Related
    upsell_ids: list[int] = Field(default_factory=list)
    cross_sell_ids: list[int] = Field(default_factory=list)

    # Advanced
    reviews_allowed: bool = True
    purchase_note: str = Field(default="", max_length=1000)
    menu_order: int = 0

    # Rank Math meta (via companion plugin)
    rank_math: RankMathMeta | None = None


class ProductUpdateRequest(BaseModel):
    """Partial update. Only provided fields are sent."""

    model_config = ConfigDict(extra="forbid")

    connection_id: int = Field(..., ge=1)

    name: str | None = Field(default=None, max_length=500)
    slug: str | None = Field(default=None, max_length=300)
    status: ProductStatus | None = None
    featured: bool | None = None
    catalog_visibility: CatalogVisibility | None = None

    description: str | None = None
    short_description: str | None = None
    sku: str | None = Field(default=None, max_length=100)

    regular_price: str | None = Field(default=None, max_length=20)
    sale_price: str | None = Field(default=None, max_length=20)
    date_on_sale_from: str | None = None
    date_on_sale_to: str | None = None
    tax_status: TaxStatus | None = None
    tax_class: str | None = Field(default=None, max_length=100)

    manage_stock: bool | None = None
    stock_quantity: int | None = Field(default=None, ge=0)
    stock_status: StockStatus | None = None
    backorders: Backorders | None = None
    low_stock_amount: int | None = Field(default=None, ge=0)
    sold_individually: bool | None = None

    weight: str | None = Field(default=None, max_length=20)
    dimensions: ProductDimensions | None = None
    shipping_class: str | None = Field(default=None, max_length=100)

    category_ids: list[int] | None = None
    tag_ids: list[int] | None = None
    images: list[ProductImageInput] | None = None

    upsell_ids: list[int] | None = None
    cross_sell_ids: list[int] | None = None

    reviews_allowed: bool | None = None
    purchase_note: str | None = Field(default=None, max_length=1000)
    menu_order: int | None = None

    rank_math: RankMathMeta | None = None


# --- Responses --------------------------------------------------------------


class ProductResponse(BaseModel):
    """Product read/write result."""

    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    slug: str
    type: str
    status: str
    permalink: str
    sku: str
    price: str
    regular_price: str
    sale_price: str

    description: str = ""
    short_description: str = ""

    featured: bool = False
    catalog_visibility: str = "visible"

    manage_stock: bool = False
    stock_quantity: int | None = None
    stock_status: str = "instock"

    weight: str = ""
    dimensions: dict[str, str] = Field(default_factory=dict)

    category_ids: list[int] = Field(default_factory=list)
    tag_ids: list[int] = Field(default_factory=list)
    image_ids: list[int] = Field(default_factory=list)
    image_urls: list[str] = Field(default_factory=list)

    menu_order: int = 0
    parent_id: int = 0

    rank_math_available: bool = False
    rank_math: RankMathMeta | None = None
    rank_math_reason: str | None = None


class ProductPublishResponse(BaseModel):
    """Result of a create or update operation."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    partial: bool = False
    wp_object_id: int | None = None
    wp_object_type: Literal["product"] = "product"
    permalink: str | None = None
    status: str | None = None
    name: str = ""
    slug: str = ""
    sku: str = ""

    rank_math_written: bool = False
    rank_math_error: str | None = None

    message: str = ""
    warnings: list[str] = Field(default_factory=list)


class ProductListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ProductResponse] = Field(default_factory=list)
    total: int = 0


class WCCategoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    slug: str
    parent: int = 0
    count: int = 0


class WCTagItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    slug: str
    count: int = 0


class WCCategoryListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[WCCategoryItem] = Field(default_factory=list)


class WCTagListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[WCTagItem] = Field(default_factory=list)