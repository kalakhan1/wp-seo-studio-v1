"""Schemas for media management."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MediaResponse(BaseModel):
    """A media item (safe to return; no secrets)."""

    model_config = ConfigDict(extra="forbid")

    id: int
    wp_media_id: int | None = None
    filename: str
    url: str | None = None
    mime: str | None = None
    size_bytes: int | None = None
    width: int | None = None
    height: int | None = None
    alt_text: str | None = None
    title: str | None = None
    caption: str | None = None
    description: str | None = None
    content_hash: str | None = None
    created_at: str
    updated_at: str


class MediaListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[MediaResponse] = Field(default_factory=list)
    total: int = 0


class MediaUpdateRequest(BaseModel):
    """Update local metadata and, if `sync_to_wordpress` is True, WP too."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    alt_text: str | None = None
    caption: str | None = None
    description: str | None = None
    sync_to_wordpress: bool = Field(
        default=True,
        description="If true, propagate changes to the WordPress media item.",
    )


class MediaUploadResponse(BaseModel):
    """Result of a media upload."""

    model_config = ConfigDict(extra="forbid")

    media: MediaResponse
    wordpress_id: int
    wordpress_url: str