"""WordPress REST API integration.

Exposes:
  - WordPressClient: composes SafeHttpClient with WordPress auth
  - Typed data models for site info, post types, taxonomies, users, media
  - WP-specific exception types
"""

from app.integrations.wordpress.client import WordPressClient
from app.integrations.wordpress.exceptions import (
    WPAuthError,
    WPClientError,
    WPConnectionError,
    WPNotFoundError,
    WPResponseError,
)
from app.integrations.wordpress.types import (
    PostType,
    SiteInfo,
    Taxonomy,
    WPMedia,
    WPUser,
)

__all__ = [
    "WordPressClient",
    "SiteInfo",
    "PostType",
    "Taxonomy",
    "WPUser",
    "WPMedia",
    "WPAuthError",
    "WPClientError",
    "WPConnectionError",
    "WPNotFoundError",
    "WPResponseError",
]