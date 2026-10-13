"""Input sanitizers.

These helpers are intentionally conservative: they strip control characters,
normalize whitespace, and cap length. They do not attempt to render HTML.
Content sanitization for posts happens at the WordPress layer via wp_kses;
on our side we only guard against obviously dangerous payloads.
"""

from __future__ import annotations

import re
import unicodedata

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_FILENAME_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


def strip_control_chars(value: str) -> str:
    """Remove ASCII control characters except tab/newline/carriage return."""
    if not value:
        return value
    normalized = unicodedata.normalize("NFKC", value)
    return _CONTROL_CHARS_RE.sub("", normalized)


def truncate(value: str, max_len: int, *, suffix: str = "") -> str:
    """Truncate a string to max_len characters, optionally appending a suffix."""
    if max_len <= 0:
        return ""
    if len(value) <= max_len:
        return value
    if suffix and len(suffix) < max_len:
        return value[: max_len - len(suffix)] + suffix
    return value[:max_len]


def sanitize_filename(filename: str, *, max_len: int = 200) -> str:
    """Produce a safe filename.

    - Strips path separators and traversal.
    - Restricts to [A-Za-z0-9._-].
    - Collapses repeated separators.
    - Preserves the extension.
    """
    if not filename:
        return "file"

    # Take only the last path segment (no traversal).
    name = filename.replace("\\", "/").split("/")[-1].strip()
    name = strip_control_chars(name)

    # Split extension.
    if "." in name:
        stem, _, ext = name.rpartition(".")
        ext = _FILENAME_SAFE_RE.sub("", ext).lower()
    else:
        stem, ext = name, ""

    stem = _FILENAME_SAFE_RE.sub("-", stem).strip("-._")
    stem = re.sub(r"-{2,}", "-", stem)
    if not stem:
        stem = "file"

    result = f"{stem}.{ext}" if ext else stem
    if len(result) > max_len:
        # Trim the stem, keep extension.
        keep = max_len - (len(ext) + 1) if ext else max_len
        keep = max(keep, 1)
        result = f"{stem[:keep]}.{ext}" if ext else stem[:max_len]
    return result