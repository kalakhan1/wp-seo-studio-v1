"""Authentication header builders for the WordPress REST API.

WordPress Application Passwords are used with HTTP Basic auth over HTTPS.
The password WordPress shows contains spaces (e.g. "abcd efgh ijkl mnop");
those spaces are part of the credential and must be preserved.
"""

from __future__ import annotations

import base64

from app.config.constants import AuthMethod
from app.core.exceptions import AuthError


def build_basic_auth_header(username: str, password: str) -> str:
    """Build an HTTP Basic auth header value."""
    if not username or not password:
        raise AuthError("Username and password are required for authentication.")
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def build_auth_headers(
    auth_method: str,
    username: str,
    password: str,
    *,
    jwt_token: str | None = None,
) -> dict[str, str]:
    """Build the appropriate authorization headers for the chosen method."""
    if auth_method in (
        AuthMethod.APPLICATION_PASSWORD.value,
        AuthMethod.BASIC.value,
    ):
        return {"Authorization": build_basic_auth_header(username, password)}
    if auth_method == AuthMethod.JWT.value:
        if not jwt_token:
            raise AuthError("JWT auth selected but no token provided.")
        return {"Authorization": f"Bearer {jwt_token}"}
    raise AuthError(f"Unsupported auth method: {auth_method!r}")