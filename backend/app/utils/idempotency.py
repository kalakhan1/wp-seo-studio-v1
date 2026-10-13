"""Idempotency key generation.

Idempotency keys are deterministic hashes of stable inputs so that repeated
submissions with identical content produce the same key. The publishing queue
uses these keys to reject duplicates.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.utils.json_safe import safe_json_dumps


def _normalize(value: Any) -> str:
    """Convert arbitrary values to a stable string representation."""
    if isinstance(value, (dict, list, tuple)):
        return safe_json_dumps(value)
    if isinstance(value, str):
        return value
    return str(value)


def make_idempotency_key(*parts: Any) -> str:
    """Return a deterministic SHA-256 hex digest of the given parts.

    Use for publish operations, e.g.:
        make_idempotency_key("product", site_url, product_slug, product_name)
    """
    hasher = hashlib.sha256()
    for part in parts:
        hasher.update(_normalize(part).encode("utf-8"))
        hasher.update(b"\x1f")  # unit separator to avoid collisions
    return hasher.hexdigest()


def make_payload_hash(payload: dict[str, Any]) -> str:
    """Hash a JSON-serializable payload with sorted keys for stability."""
    try:
        serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        serialized = safe_json_dumps(payload)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()