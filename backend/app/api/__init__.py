"""API package: dependencies and versioned routers."""

from app.api.deps import (
    get_request_id,
    get_settings_dep,
    get_wp_client_placeholder,
)

__all__ = [
    "get_request_id",
    "get_settings_dep",
    "get_wp_client_placeholder",
]