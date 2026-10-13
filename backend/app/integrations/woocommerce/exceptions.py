"""WooCommerce-specific exceptions."""

from __future__ import annotations

from app.core.exceptions import AppError


class WooClientError(AppError):
    """Generic WooCommerce client error."""

    code = "WOO_CLIENT_ERROR"
    http_status = 502


class WooConnectionError(WooClientError):
    """Could not reach the WooCommerce REST API."""

    code = "WOO_CONNECTION_ERROR"
    http_status = 502


class WooAuthError(WooClientError):
    """WooCommerce authentication failed (401, 403)."""

    code = "WOO_AUTH_ERROR"
    http_status = 401


class WooNotFoundError(WooClientError):
    """WooCommerce endpoint not found (404). Usually means WC is not active."""

    code = "WOO_NOT_FOUND"
    http_status = 404


class WooResponseError(WooClientError):
    """WooCommerce returned an unexpected response."""

    code = "WOO_RESPONSE_ERROR"
    http_status = 502