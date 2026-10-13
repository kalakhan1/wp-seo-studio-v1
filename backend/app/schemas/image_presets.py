"""Schemas for image presets and archive grid CSS presets."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


AspectRatio = Literal["1:1", "4:5", "3:4", "4:3", "3:2", "16:9", "2:3", "custom"]
ObjectFit = Literal["cover", "contain", "fill", "none", "scale-down"]
ObjectPosition = Literal[
    "center", "top", "bottom", "left", "right", "custom"
]


class RegisteredImageSize(BaseModel):
    """A WordPress registered image size as discovered from a media item."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        description="Size slug registered by WordPress or a plugin.",
        examples=["thumbnail", "woocommerce_thumbnail"],
    )
    width: int = Field(..., ge=0)
    height: int = Field(..., ge=0)
    crop: bool = Field(
        default=False,
        description="Whether WordPress crops to exactly these dimensions.",
    )


class SuggestedPreset(BaseModel):
    """A suggested preset for a common use case."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(
        ...,
        description="Stable preset key.",
        examples=["product_card"],
    )
    label: str = Field(..., examples=["Product card"])
    description: str = ""
    width: int = Field(..., ge=1)
    height: int = Field(..., ge=1)
    crop: bool = True
    aspect_ratio: AspectRatio = "1:1"


class CSSPreset(BaseModel):
    """A CSS display preset for a container.

    This controls how the browser displays images. It does NOT change the
    image file or its WordPress derivatives.
    """

    model_config = ConfigDict(extra="forbid")

    key: str = Field(
        ...,
        description="Stable preset key.",
        examples=["square_cover"],
    )
    label: str = Field(..., examples=["Square, cover"])
    description: str = ""
    aspect_ratio: AspectRatio = "1:1"
    object_fit: ObjectFit = "cover"
    object_position: ObjectPosition = "center"
    border_radius: str = "0"
    background: str = "#f8fafc"


class DiscoveredSizesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_media_id: int
    source_media_url: str = ""
    sizes: list[RegisteredImageSize] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PresetsResponse(BaseModel):
    """All presets the app knows about, plus any discovered on the site."""

    model_config = ConfigDict(extra="forbid")

    suggested: list[SuggestedPreset] = Field(default_factory=list)
    css: list[CSSPreset] = Field(default_factory=list)


class CustomPresetRequest(BaseModel):
    """Build a custom preset from user-provided values."""

    model_config = ConfigDict(extra="forbid")

    width: int = Field(..., ge=1, le=10000)
    height: int = Field(..., ge=1, le=10000)
    crop: bool = True
    aspect_ratio: AspectRatio = "custom"