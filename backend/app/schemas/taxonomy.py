"""Schemas for taxonomy endpoints (categories, tags)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.integrations.wordpress.types import WPCategory, WPTag


class CategoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    slug: str
    parent: int = 0
    count: int = 0


class TagItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    slug: str
    count: int = 0


class CategoryListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[CategoryItem] = Field(default_factory=list)


class TagListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[TagItem] = Field(default_factory=list)


def category_from_wp(c: WPCategory) -> CategoryItem:
    return CategoryItem(
        id=c.id,
        name=c.name,
        slug=c.slug,
        parent=c.parent,
        count=c.count,
    )


def tag_from_wp(t: WPTag) -> TagItem:
    return TagItem(id=t.id, name=t.name, slug=t.slug, count=t.count)