"""Typed data models for WordPress REST API responses.

Only the fields the application uses are typed. Unknown fields are
ignored on parsing and are never stored, to avoid leaking unexpected
data into our local database or logs.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SiteInfo(BaseModel):
    """Response from GET /wp-json."""

    model_config = ConfigDict(extra="ignore")

    name: str = ""
    description: str = ""
    url: str = ""
    home: str = ""
    gmt_offset: float = 0.0
    timezone_string: str = ""
    namespaces: list[str] = Field(default_factory=list)


class PostType(BaseModel):
    """Post type from GET /wp-json/wp/v2/types."""

    model_config = ConfigDict(extra="ignore")

    slug: str
    name: str = ""
    rest_base: str = ""
    rest_namespace: str = ""
    hierarchical: bool = False
    supports: list[str] = Field(default_factory=list)


class Taxonomy(BaseModel):
    """Taxonomy from GET /wp-json/wp/v2/taxonomies."""

    model_config = ConfigDict(extra="ignore")

    slug: str
    name: str = ""
    rest_base: str = ""
    rest_namespace: str = ""
    hierarchical: bool = False
    types: list[str] = Field(default_factory=list)


class WPUser(BaseModel):
    """User from GET /wp-json/wp/v2/users/me."""

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str = ""
    slug: str = ""
    roles: list[str] = Field(default_factory=list)
    capabilities: dict[str, bool] = Field(default_factory=dict)


class WPMedia(BaseModel):
    """Media item from /wp-json/wp/v2/media."""

    model_config = ConfigDict(extra="ignore")

    id: int
    title: dict[str, Any] = Field(default_factory=dict)
    caption: dict[str, Any] = Field(default_factory=dict)
    description: dict[str, Any] = Field(default_factory=dict)
    alt_text: str = ""
    source_url: str = ""
    mime_type: str = ""
    media_details: dict[str, Any] = Field(default_factory=dict)

    def rendered_title(self) -> str:
        return str(self.title.get("rendered", "") or "")

    def rendered_caption(self) -> str:
        return str(self.caption.get("rendered", "") or "")

    def rendered_description(self) -> str:
        return str(self.description.get("rendered", "") or "")

    def width(self) -> int | None:
        w = self.media_details.get("width")
        return int(w) if isinstance(w, (int, float)) else None

    def height(self) -> int | None:
        h = self.media_details.get("height")
        return int(h) if isinstance(h, (int, float)) else None


class WPCategory(BaseModel):
    """Category from GET /wp-json/wp/v2/categories."""

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str = ""
    slug: str = ""
    description: str = ""
    parent: int = 0
    count: int = 0


class WPTag(BaseModel):
    """Tag from GET /wp-json/wp/v2/tags."""

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str = ""
    slug: str = ""
    description: str = ""
    count: int = 0


class WPPost(BaseModel):
    """Post or page from /wp-json/wp/v2/posts or /pages.

    WordPress returns nested dicts for title/content/excerpt with
    `rendered` always present, and `raw` present when context=edit. We
    keep the raw dicts so callers can choose.

    `status` values: draft, publish, future, pending, private, trash.
    `type` is "post" or "page".
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    type: str = ""
    status: str = ""
    slug: str = ""
    link: str = ""

    title: dict[str, Any] = Field(default_factory=dict)
    content: dict[str, Any] = Field(default_factory=dict)
    excerpt: dict[str, Any] = Field(default_factory=dict)

    author: int = 0
    featured_media: int = 0
    parent: int = 0
    menu_order: int = 0
    comment_status: str = ""
    ping_status: str = ""

    categories: list[int] = Field(default_factory=list)
    tags: list[int] = Field(default_factory=list)

    date: str = ""
    date_gmt: str = ""
    modified: str = ""
    modified_gmt: str = ""

    # -- Convenience helpers ------------------------------------------------

    def rendered_title(self) -> str:
        return str(self.title.get("rendered", "") or "")

    def raw_title(self) -> str:
        return str(self.title.get("raw", self.title.get("rendered", "")) or "")

    def rendered_content(self) -> str:
        return str(self.content.get("rendered", "") or "")

    def raw_content(self) -> str:
        return str(self.content.get("raw", self.content.get("rendered", "")) or "")

    def rendered_excerpt(self) -> str:
        return str(self.excerpt.get("rendered", "") or "")

    def raw_excerpt(self) -> str:
        return str(self.excerpt.get("raw", self.excerpt.get("rendered", "")) or "")