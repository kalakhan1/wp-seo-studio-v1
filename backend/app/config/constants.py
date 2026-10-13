"""Application-wide constants and enums.

These enums are shared across the backend and mirrored in the frontend
TypeScript types. Keep them stable; add new members only, never rename
existing ones without a migration note in docs/.
"""

from __future__ import annotations

from enum import Enum


class AppEnv(str, Enum):
    """Deployment environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class AppMode(str, Enum):
    """Runtime mode for external integrations.

    MOCK -> No real WordPress/WooCommerce calls. Uses in-memory mock clients.
    REAL -> Calls the configured WordPress/WooCommerce endpoints.
    """

    MOCK = "mock"
    REAL = "real"


class LogFormat(str, Enum):
    """Log output format."""

    HUMAN = "human"
    JSON = "json"


class AuthMethod(str, Enum):
    """WordPress authentication method."""

    APPLICATION_PASSWORD = "application_password"
    JWT = "jwt"  # reserved for future
    BASIC = "basic"  # discouraged; HTTPS only
    NONE = "none"


class WPObjectType(str, Enum):
    """WordPress / WooCommerce object types."""

    POST = "post"
    PAGE = "page"
    PRODUCT = "product"
    MEDIA = "media"
    CATEGORY = "category"
    TAG = "tag"
    USER = "user"


class OperationType(str, Enum):
    """Operation types logged in history."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    PUBLISH = "publish"
    SCHEDULE = "schedule"
    UPLOAD = "upload"
    AUDIT = "audit"
    SETTINGS_UPDATE = "settings_update"


class JobStatus(str, Enum):
    """Publishing queue job status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class CapabilityStatus(str, Enum):
    """Capability discovery classification.

    SUPPORTED               -> Read/write works with current credentials.
    READ_ONLY               -> Read works, write fails or unverified.
    REQUIRES_ELEVATED       -> Needs higher WordPress role.
    REQUIRES_PLUGIN         -> Needs companion plugin or premium plugin.
    REQUIRES_MANUAL_SETUP   -> Needs admin action in WP dashboard.
    NOT_VERIFIED            -> Could not be tested safely.
    UNSUPPORTED             -> Not exposed by REST API or blocked.
    """

    SUPPORTED = "supported"
    READ_ONLY = "read_only"
    REQUIRES_ELEVATED = "requires_elevated"
    REQUIRES_PLUGIN = "requires_plugin"
    REQUIRES_MANUAL_SETUP = "requires_manual_setup"
    NOT_VERIFIED = "not_verified"
    UNSUPPORTED = "unsupported"


# --- Defaults ---------------------------------------------------------------

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_LOG_LEVEL = "info"
DEFAULT_HTTP_TIMEOUT = 30
DEFAULT_HTTP_MAX_RETRIES = 3
DEFAULT_MAX_RESPONSE_BYTES = 10 * 1024 * 1024  # 10 MB

# --- Secret masking ---------------------------------------------------------

SECRET_KEY_PATTERNS = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "auth",
    "credential",
    "private_key",
    "consumer_key",
    "consumer_secret",
)

MASKED_VALUE = "***MASKED***"

# --- SSRF guard -------------------------------------------------------------

BLOCKED_SCHEMES = ("file", "ftp", "gopher", "data", "javascript", "vbscript")
BLOCKED_HOSTNAMES = ("localhost", "localhost.localdomain", "ip6-localhost")

# --- Rate limiting ----------------------------------------------------------

DEFAULT_RATE_LIMIT_PER_HOST = 30  # requests
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 60

# --- API --------------------------------------------------------------------

API_V1_PREFIX = "/api/v1"