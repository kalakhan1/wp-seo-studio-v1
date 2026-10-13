"""Schemas for Rank Math global settings.

Rank Math stores its global settings in a single WordPress option array.
The companion plugin exposes only the fields we have verified, and
refuses to write to any key not in its allowlist.

Fields shown here are conservative: they are documented in Rank Math and
stable across recent versions. Advanced or premium-only options are not
exposed.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RankMathSettings(BaseModel):
    """Subset of Rank Math global settings exposed to the app."""

    model_config = ConfigDict(extra="ignore")

    # --- Titles & Meta ---
    title_separator: str = "|"
    homepage_title: str = ""
    homepage_description: str = ""

    # --- Sitemap ---
    sitemap_enabled: bool = True
    sitemap_include_products: bool = True
    sitemap_include_posts: bool = True
    sitemap_include_pages: bool = True

    # --- Indexing / Robots ---
    noindex_empty_category: bool = False
    noindex_search: bool = True
    noindex_author_archives: bool = True
    noindex_date_archives: bool = True

    # --- Breadcrumbs ---
    breadcrumbs_enabled: bool = False

    # --- WooCommerce ---
    wc_remove_category_base: bool = False
    wc_show_product_breadcrumbs: bool = True


RankMathOptionKey = Literal[
    "titles",
    "sitemap",
    "noindex",
    "breadcrumbs",
    "woocommerce",
]


class RankMathSettingsResponse(BaseModel):
    """Global settings plus discovery metadata."""

    model_config = ConfigDict(extra="forbid")

    settings: RankMathSettings
    discovered_at: str
    rank_math_version: str = ""
    source: Literal["companion", "unavailable"] = "companion"
    reason: str = ""
    warnings: list[str] = Field(default_factory=list)


class RankMathSettingUpdateRequest(BaseModel):
    """Update one or more settings fields. Only provided fields are written."""

    model_config = ConfigDict(extra="forbid")

    title_separator: str | None = Field(default=None, max_length=5)
    homepage_title: str | None = Field(default=None, max_length=500)
    homepage_description: str | None = Field(default=None, max_length=500)
    sitemap_enabled: bool | None = None
    sitemap_include_products: bool | None = None
    sitemap_include_posts: bool | None = None
    sitemap_include_pages: bool | None = None
    noindex_empty_category: bool | None = None
    noindex_search: bool | None = None
    noindex_author_archives: bool | None = None
    noindex_date_archives: bool | None = None
    breadcrumbs_enabled: bool | None = None
    wc_remove_category_base: bool | None = None
    wc_show_product_breadcrumbs: bool | None = None


class RankMathSettingsUpdateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    settings: RankMathSettings
    changed: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RankMathCapabilityStatus(BaseModel):
    """Readiness summary for the settings UI."""

    model_config = ConfigDict(extra="forbid")

    plugin_available: bool
    rank_math_active: bool
    version: str = ""
    readable_keys: list[str] = Field(default_factory=list)
    reason: str = ""
    evidence: dict[str, Any] = Field(default_factory=dict)