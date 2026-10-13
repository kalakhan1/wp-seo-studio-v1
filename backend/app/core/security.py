"""Secret masking helpers.

No secrets are ever logged or returned. `mask_dict` walks nested structures
and replaces values whose key looks secret-like.
"""

from __future__ import annotations

from typing import Any, Mapping

from app.config.constants import MASKED_VALUE, SECRET_KEY_PATTERNS


def is_secret_key(key: str) -> bool:
    """Return True if a key name looks like it holds a secret."""
    lowered = key.lower()
    return any(pattern in lowered for pattern in SECRET_KEY_PATTERNS)


def mask_string(value: str, *, keep_prefix: int = 2, keep_suffix: int = 2) -> str:
    """Mask a string, optionally keeping a small hint of the original.

    Used only for display; never used for logs.
    """
    if not value:
        return ""
    if len(value) <= keep_prefix + keep_suffix:
        return MASKED_VALUE
    return f"{value[:keep_prefix]}{MASKED_VALUE}{value[-keep_suffix:]}"


def mask_value(value: Any) -> Any:
    """Recursively mask nested structures. Unknown keys pass through unchanged."""
    if isinstance(value, Mapping):
        return {
            k: (MASKED_VALUE if is_secret_key(str(k)) else mask_value(v))
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [mask_value(v) for v in value]
    if isinstance(value, set):
        return {mask_value(v) for v in value}
    if isinstance(value, str) and len(value) > 512:
        return value[:256] + "...<truncated>"
    return value


def mask_dict(data: Mapping[str, Any]) -> dict[str, Any]:
    """Mask a dict (typically settings.model_dump()) for safe logging/display."""
    return {k: (MASKED_VALUE if is_secret_key(str(k)) else mask_value(v)) for k, v in data.items()}