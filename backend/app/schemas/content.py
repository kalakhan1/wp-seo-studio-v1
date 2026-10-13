"""Schemas for WordPress posts and pages.

Supports both posts and pages through a single `kind` discriminator.
Rank Math meta (SEO title, description, focus keyword, etc.) is optional
and written via the companion plugin.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.integrations.rankmath.types import RankMathMeta


ContentKind = Literal["post", "page"]
ContentStatus = Literal["draft", "publish", "future", "pending", "private"]


# --- Create -----------------------------------------------------------------


class ContentCreateRequest(BaseModel):
    """Create a new WordPress post or page."""

    model_config = ConfigDict(extra="forbid")

    connection_id: int = Field(..., ge=1)

    kind: ContentKind = Field(
        ...,
        description="Object kind. 'post' or 'page'.",
        examples=["post"],
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Post or page title.",
        examples=["Badam Benefits Guide"],
    )
    slug: str = Field(
        default="",
        max_length=300,
        description="URL slug. Leave empty to let WordPress generate one.",
        examples=["badam-benefits-guide"],
    )
    content: str = Field(
        default="",
        description="Post content (HTML allowed; sanitized by WordPress).",
        examples=["<p>Badam is a nutrient-dense nut.</p>"],
    )
    excerpt: str = Field(
        default="",
        description="Short excerpt (posts only).",
        examples=["A practical guide to badam."],
    )
    status: ContentStatus = Field(
        default="draft",
        description="Publication status.",
        examples=["draft"],
    )
    scheduled_date: str | None = Field(
        default=None,
        description=(
            "ISO 8601 date for scheduled publication. "
            "Required when status is 'future'."
        ),
        examples=["2026-11-01T10:00:00"],
    )

    # Optional targeting fields
    author_id: int | None = Field(
        default=None,
        description="WordPress user id for the author. Defaults to current user.",
    )
    featured_media_id: int | None = Field(
        default=None,
        description="WordPress media id for the featured image.",
    )
    categories: list[int] = Field(
        default_factory=list,
        description="Category IDs (posts only).",
    )
    tags: list[int] = Field(
        default_factory=list,
        description="Tag IDs (posts only).",
    )
    parent_id: int | None = Field(
        default=None,
        description="Parent page id (pages only).",
    )
    menu_order: int = Field(default=0, ge=-9999, le=9999)
    comment_status: Literal["open", "closed"] = "open"
    ping_status: Literal["open", "closed"] = "open"

    # Rank Math meta
    rank_math: RankMathMeta | None = Field(
        default=None,
        description=(
            "Rank Math SEO metadata. Written via the companion plugin. "
            "If the plugin is not installed, content is still created and "
            "a warning is returned."
        ),
    )

    @field_validator("scheduled_date")
    @classmethod
    def _validate_scheduled_date(cls, value: str | None, info) -> str | None:  # type: ignore[no-untyped-def]
        status = info.data.get("status")
        if status == "future" and not value:
            raise ValueError("scheduled_date is required when status is 'future'.")
        return value


class ContentUpdateRequest(BaseModel):
    """Partial update. Only provided fields are sent to WordPress."""

    model_config = ConfigDict(extra="forbid")

    connection_id: int = Field(..., ge=1)

    title: str | None = Field(default=None, max_length=500)
    slug: str | None = Field(default=None, max_length=300)
    content: str | None = None
    excerpt: str | None = None
    status: ContentStatus | None = None
    scheduled_date: str | None = None

    featured_media_id: int | None = None
    categories: list[int] | None = None
    tags: list[int] | None = None
    parent_id: int | None = None
    menu_order: int | None = Field(default=None, ge=-9999, le=9999)
    comment_status: Literal["open", "closed"] | None = None
    ping_status: Literal["open", "closed"] | None = None

    rank_math: RankMathMeta | None = None


# --- Responses --------------------------------------------------------------


class ContentPublishResponse(BaseModel):
    """Result of a create or update operation.

    `partial` is True when the WordPress object was written but a follow-up
    step (like Rank Math meta) failed. The caller can retry just the meta
    without re-creating the object.
    """

    model_config = ConfigDict(extra="forbid")

    success: bool
    partial: bool = Field(
        default=False,
        description="True when the object was written but a secondary step failed.",
    )
    wp_object_id: int | None = None
    wp_object_type: ContentKind
    permalink: str | None = None
    status: str | None = None
    title: str = ""
    slug: str = ""

    rank_math_written: bool = False
    rank_math_error: str | None = None

    message: str = ""
    warnings: list[str] = Field(default_factory=list)


class ContentGetResponse(BaseModel):
    """Full post/page with Rank Math meta when available."""

    model_config = ConfigDict(extra="forbid")

    id: int
    kind: ContentKind
    status: str
    slug: str
    permalink: str
    title: str
    content: str
    excerpt: str

    author_id: int = 0
    featured_media_id: int = 0
    parent_id: int = 0
    menu_order: int = 0
    comment_status: str = ""
    ping_status: str = ""

    categories: list[int] = Field(default_factory=list)
    tags: list[int] = Field(default_factory=list)

    date: str = ""
    modified: str = ""

    rank_math: RankMathMeta | None = None
    rank_math_available: bool = False
    rank_math_reason: str | None = None


class ContentListResponse(BaseModel):
    """List response (from local publish history, not from WordPress)."""

    model_config = ConfigDict(extra="forbid")

    items: list[ContentPublishResponse] = Field(default_factory=list)
    total: int = 0