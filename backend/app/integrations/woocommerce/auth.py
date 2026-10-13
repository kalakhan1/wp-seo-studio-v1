"""WooCommerce REST API authentication.

WooCommerce REST API uses HTTP Basic auth with a consumer key and secret
over HTTPS. The same scheme is used as for WordPress Application Passwords,
just with different credentials.
"""

from __future__ import annotations

import base64

from app.core.exceptions import AuthError


def build_wc_basic_auth_header(consumer_key: str, consumer_secret: str) -> str:
    """Build an HTTP Basic auth header value for WooCommerce."""
    if not consumer_key or not consumer_secret:
        raise AuthError(
            "WooCommerce consumer key and secret are required.",
        )
    token = base64.b64encode(
        f"{consumer_key}:{consumer_secret}".encode("utf-8"),
    ).decode("ascii")
    return f"Basic {token}"