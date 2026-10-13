"""Image presets service.

Responsibilities:
  - Return a curated list of suggested presets for a WooCommerce herbal store.
  - Return a curated list of CSS display presets for balanced archive grids.
  - Discover registered image sizes by inspecting an existing media item
    on the connected site (WordPress exposes `media_details.sizes` there).

Nothing here modifies the site. All presets are advisory; the UI decides
how to apply them.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.core.exceptions import AuthError, ValidationError
from app.integrations.wordpress.client import WordPressClient
from app.models.connection import Connection
from app.schemas.image_presets import (
    CSSPreset,
    DiscoveredSizesResponse,
    PresetsResponse,
    RegisteredImageSize,
    SuggestedPreset,
)
from app.security import secrets as secret_store

# --- Curated suggested presets ---------------------------------------------

SUGGESTED_PRESETS: list[SuggestedPreset] = [
    SuggestedPreset(
        key="product_card",
        label="Product card",
        description=(
            "Consistent display area for product images on archive pages. "
            "Square, cropped to fill."
        ),
        width=600,
        height=600,
        crop=True,
        aspect_ratio="1:1",
    ),
    SuggestedPreset(
        key="product_detail",
        label="Product detail image",
        description=(
            "Large product image on the single product page. "
            "Landscape, mild crop."
        ),
        width=1000,
        height=750,
        crop=True,
        aspect_ratio="4:3",
    ),
    SuggestedPreset(
        key="gallery_thumbnail",
        label="Gallery thumbnail",
        description="Small gallery thumbnail below the main product image.",
        width=200,
        height=200,
        crop=True,
        aspect_ratio="1:1",
    ),
    SuggestedPreset(
        key="blog_featured",
        label="Blog featured image",
        description=(
            "Wide hero image at the top of a blog post or on archive cards."
        ),
        width=1200,
        height=675,
        crop=True,
        aspect_ratio="16:9",
    ),
    SuggestedPreset(
        key="blog_inline",
        label="Blog inline image",
        description=(
            "Image placed inside article content. Wide but not too tall."
        ),
        width=900,
        height=600,
        crop=True,
        aspect_ratio="3:2",
    ),
    SuggestedPreset(
        key="social_share",
        label="Social sharing image",
        description=(
            "Facebook/Twitter sharing preview. Keep the subject near the "
            "center; edges may be cropped by the platform."
        ),
        width=1200,
        height=630,
        crop=True,
        aspect_ratio="16:9",
    ),
]


# --- Curated CSS display presets -------------------------------------------

CSS_PRESETS: list[CSSPreset] = [
    CSSPreset(
        key="square_cover",
        label="Square, cover",
        description=(
            "Fixed square container, image fills and crops. Best for a "
            "balanced product archive grid."
        ),
        aspect_ratio="1:1",
        object_fit="cover",
        object_position="center",
    ),
    CSSPreset(
        key="square_contain",
        label="Square, contain",
        description=(
            "Square container, image fully visible with padding. Use when "
            "cropping would hide product packaging details."
        ),
        aspect_ratio="1:1",
        object_fit="contain",
        object_position="center",
    ),
    CSSPreset(
        key="portrait_4_5_cover",
        label="Portrait 4:5, cover",
        description="Taller product cards, good for fashion or bottles.",
        aspect_ratio="4:5",
        object_fit="cover",
        object_position="center",
    ),
    CSSPreset(
        key="landscape_16_9_cover",
        label="Landscape 16:9, cover",
        description="Wide cards, suits banners and blog thumbnails.",
        aspect_ratio="16:9",
        object_fit="cover",
        object_position="center",
    ),
    CSSPreset(
        key="rounded_square",
        label="Rounded square",
        description="Square with rounded corners for a soft look.",
        aspect_ratio="1:1",
        object_fit="cover",
        object_position="center",
        border_radius="12px",
    ),
]


class ImagePresetsService:
    """Stateless. Construct per request with settings + session."""

    def __init__(self, *, settings: Settings, session: AsyncSession) -> None:
        self._settings = settings
        self._session = session

    # --- Static presets ----------------------------------------------------

    async def list_presets(self) -> PresetsResponse:
        return PresetsResponse(
            suggested=SUGGESTED_PRESETS,
            css=CSS_PRESETS,
        )

    # --- Discovered sizes --------------------------------------------------

    async def discover_registered_sizes(
        self,
        *,
        connection_id: int,
        media_id: int | None,
        http: Any,
    ) -> DiscoveredSizesResponse:
        """Discover registered image sizes from WordPress.

        If `media_id` is not provided, the most recent image is used.
        WordPress exposes registered sizes only through a media item's
        `media_details.sizes` map, so we always inspect an item.
        """
        wp = await self._wp_client(connection_id, http)

        warnings: list[str] = []
        target_id = media_id

        if target_id is None:
            recent = await wp.list_media(per_page=1)
            if not recent:
                return DiscoveredSizesResponse(
                    source_media_id=0,
                    sizes=[],
                    warnings=[
                        "No media items found. Upload at least one image to "
                        "discover registered sizes."
                    ],
                )
            target_id = recent[0].id

        media = await wp.get_media(target_id)
        details = media.media_details or {}
        sizes_map = details.get("sizes")
        if not isinstance(sizes_map, dict):
            sizes_map = {}

        result: list[RegisteredImageSize] = []
        for name, entry in sizes_map.items():
            if not isinstance(entry, dict):
                continue
            w = entry.get("width")
            h = entry.get("height")
            if not isinstance(w, (int, float)) or not isinstance(h, (int, float)):
                continue
            result.append(
                RegisteredImageSize(
                    name=str(name),
                    width=int(w),
                    height=int(h),
                    crop=bool(entry.get("crop", False)),
                )
            )

        result.sort(key=lambda s: (s.width, s.height, s.name))

        if not result:
            warnings.append(
                "WordPress did not return any registered sizes for this "
                "media item. This may mean the image derivatives have not "
                "been generated yet."
            )

        return DiscoveredSizesResponse(
            source_media_id=media.id,
            source_media_url=media.source_url,
            sizes=result,
            warnings=warnings,
        )

    # --- Internals ---------------------------------------------------------

    async def _require_connection(self, connection_id: int) -> Connection:
        result = await self._session.execute(
            select(Connection).where(Connection.id == connection_id)
        )
        c = result.scalar_one_or_none()
        if c is None:
            raise ValidationError(
                "Connection not found.",
                details={"connection_id": connection_id},
            )
        return c

    async def _wp_client(
        self, connection_id: int, http: Any
    ) -> WordPressClient:
        c = await self._require_connection(connection_id)
        label = c.secret_ref or c.label
        password = secret_store.get_secret(
            label, secret_store.FIELD_WP_APP_PASSWORD
        )
        if not password:
            raise AuthError(
                "Stored WordPress credentials are missing from the OS keyring.",
                details={"label": label},
            )
        return WordPressClient(
            base_url=c.base_url,
            username=c.username,
            app_password=password,
            auth_method=c.auth_method,
            http=http,
        )