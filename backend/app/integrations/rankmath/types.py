"""Types for Rank Math metadata.

The field set matches the companion plugin exactly. Any field not in this
model is ignored on read and cannot be written — the plugin ignores
unknown keys as well.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RankMathMeta(BaseModel):
    """Rank Math per-post SEO metadata.

    All fields are optional. A None value means "no change" on write, and
    "not set" on read.
    """

    model_config = ConfigDict(extra="ignore")

    title: str | None = Field(
        default=None,
        description="Rank Math SEO title.",
        examples=["Herbal Hair Oil for Daily Care"],
    )
    description: str | None = Field(
        default=None,
        description="Meta description.",
        examples=["Natural herbal hair oil for daily care."],
    )
    focus_keyword: str | None = Field(
        default=None,
        description="Rank Math focus keyword.",
        examples=["herbal hair oil"],
    )
    canonical_url: str | None = Field(
        default=None,
        description="Custom canonical URL override.",
    )
    robots: list[str] = Field(
        default_factory=list,
        description="Robots directives (e.g. ['index', 'follow']).",
    )
    facebook_title: str | None = None
    facebook_description: str | None = None
    facebook_image: str | None = None
    twitter_title: str | None = None
    twitter_description: str | None = None
    twitter_image: str | None = None

    def provided_fields(self) -> dict[str, object]:
        """Return only the fields that have an explicit value (or non-empty list)."""
        out: dict[str, object] = {}
        data = self.model_dump(exclude_unset=True, exclude_none=True)
        # Include empty list only if explicitly set — model_dump already
        # excludes unset fields; keep robots if present in `data`.
        for key, value in data.items():
            out[key] = value
        return out