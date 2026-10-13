"""OS keyring wrapper for storing WordPress and WooCommerce credentials.

Uses the `keyring` library, which on Windows stores secrets in Credential
Manager, on macOS in Keychain, on Linux in Secret Service / KWallet.

Secrets are NEVER written to the database. The `connections` table only
stores a stable label; keyring entries are looked up by that label.
"""

from __future__ import annotations

from keyring import get_password, set_password
from keyring.errors import KeyringError

from app.config.logging import get_logger

_SERVICE_NAME = "wp-seo-studio"

_log = get_logger(__name__)

# Field names used in keyring keys. Kept stable across phases.
FIELD_WP_APP_PASSWORD = "wp_app_password"
FIELD_WC_CONSUMER_KEY = "wc_consumer_key"
FIELD_WC_CONSUMER_SECRET = "wc_consumer_secret"


def _key(label: str, field: str) -> str:
    """Keyring key for a given connection label and secret field."""
    return f"conn:{label}:{field}"


def set_secret(label: str, field: str, value: str) -> None:
    """Store a secret. Overwrites any existing value."""
    if not label:
        raise ValueError("label is required")
    if not value:
        # Empty values should be removed rather than stored.
        delete_secret(label, field)
        return
    try:
        set_password(_SERVICE_NAME, _key(label, field), value)
    except KeyringError as exc:
        raise RuntimeError(
            f"Could not store secret in OS keyring: {exc.__class__.__name__}"
        ) from exc


def get_secret(label: str, field: str) -> str | None:
    """Retrieve a secret. Returns None if missing or keyring unavailable."""
    if not label:
        return None
    try:
        return get_password(_SERVICE_NAME, _key(label, field))
    except KeyringError as exc:
        _log.warning(
            "keyring_read_failed",
            label=label,
            field=field,
            error=exc.__class__.__name__,
        )
        return None


def delete_secret(label: str, field: str) -> None:
    """Delete a secret. Silent if missing."""
    if not label:
        return
    try:
        from keyring import delete_password  # local import to keep top tidy

        delete_password(_SERVICE_NAME, _key(label, field))
    except KeyringError:
        # Already gone, or keyring unavailable. Silent by design.
        return
    except Exception as exc:  # noqa: BLE001
        _log.warning(
            "keyring_delete_failed",
            label=label,
            field=field,
            error=exc.__class__.__name__,
        )


def delete_all_for_label(label: str) -> None:
    """Delete every known secret for a connection label."""
    for field in (
        FIELD_WP_APP_PASSWORD,
        FIELD_WC_CONSUMER_KEY,
        FIELD_WC_CONSUMER_SECRET,
    ):
        delete_secret(label, field)