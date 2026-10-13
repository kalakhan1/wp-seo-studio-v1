"""In-memory mock WordPress client.

Mirrors the public interface of app.integrations.wordpress.WordPressClient
so callers (tests and, in the future, a runtime mock-mode client) can swap
between the two without any other change.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.integrations.wordpress.types import (
    PostType,
    SiteInfo,
    Taxonomy,
    WPMedia,
    WPUser,
)
from tests.mocks.mock_wordpress.routes import MockWordPressRoutes


@dataclass
class MockWordPressClient:
    """Deterministic, in-memory stand-in for a WordPress REST client."""

    base_url: str = "https://example.test"
    username: str = "demo"
    routes: MockWordPressRoutes = field(default_factory=MockWordPressRoutes)

    # --- Public API (matches real WordPressClient) ------------------------

    async def get_site_info(self) -> SiteInfo:
        return self.routes.site_info.model_copy()

    async def get_current_user(self) -> WPUser:
        return self.routes.current_user.model_copy()

    async def list_post_types(self) -> list[PostType]:
        return [pt.model_copy() for pt in self.routes.post_types]

    async def list_taxonomies(self) -> list[Taxonomy]:
        return [t.model_copy() for t in self.routes.taxonomies]

    async def list_media(self, *, per_page: int = 5) -> list[WPMedia]:
        return [m.model_copy() for m in self.routes.media[:per_page]]

    # --- Helpers ----------------------------------------------------------

    def reset(self) -> None:
        """Reset the mock to its initial state."""
        self.routes = MockWordPressRoutes()