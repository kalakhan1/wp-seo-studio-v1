"""Exception hierarchy for the application.

Every application-level error inherits from AppError so the API layer can
serialize it consistently. Unexpected errors remain as-is and are handled
by the global exception handler.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base class for all application errors.

    Attributes:
        code: Machine-readable error code (e.g. 'CONFIG_ERROR').
        message: Human-readable message safe to show to the user.
        details: Optional structured details (never contains secrets).
        http_status: Suggested HTTP status code for the API layer.
    """

    code: str = "APP_ERROR"
    http_status: int = 500

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        http_status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        if http_status is not None:
            self.http_status = http_status

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"


class ConfigError(AppError):
    """Raised when configuration is invalid or missing."""

    code = "CONFIG_ERROR"
    http_status = 500


class AuthError(AppError):
    """Raised when authentication fails or credentials are missing."""

    code = "AUTH_ERROR"
    http_status = 401


class ValidationError(AppError):
    """Raised when input validation fails at the application layer."""

    code = "VALIDATION_ERROR"
    http_status = 422


class SSRFBlockedError(AppError):
    """Raised when a request targets a blocked (private/internal) address."""

    code = "SSRF_BLOCKED"
    http_status = 400


class RateLimitError(AppError):
    """Raised when a rate limit is exceeded."""

    code = "RATE_LIMIT_EXCEEDED"
    http_status = 429


class WPError(AppError):
    """Raised for WordPress REST API failures."""

    code = "WP_ERROR"
    http_status = 502


class WooError(AppError):
    """Raised for WooCommerce REST API failures."""

    code = "WOO_ERROR"
    http_status = 502


class JobError(AppError):
    """Raised for publishing queue / background job failures."""

    code = "JOB_ERROR"
    http_status = 500