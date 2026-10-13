"""WordPress-specific exceptions.

These extend the core AppError hierarchy so the API layer can serialize
them with consistent error codes and HTTP statuses.
"""

from __future__ import annotations

from app.core.exceptions import AppError


class WPClientError(AppError):
    """Generic WordPress client error."""

    code = "WP_CLIENT_ERROR"
    http_status = 502


class WPConnectionError(WPClientError):
    """Could not reach the WordPress site (transport, DNS, timeout)."""

    code = "WP_CONNECTION_ERROR"
    http_status = 502


class WPAuthError(WPClientError):
    """Authentication failed (401, 403)."""

    code = "WP_AUTH_ERROR"
    http_status = 401


class WPNotFoundError(WPClientError):
    """Requested resource was not found (404)."""

    code = "WP_NOT_FOUND"
    http_status = 404


class WPResponseError(WPClientError):
    """WordPress returned an unexpected response (5xx, malformed JSON)."""

    code = "WP_RESPONSE_ERROR"
    http_status = 502