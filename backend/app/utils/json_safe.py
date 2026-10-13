"""JSON helpers.

`safe_json_loads` never raises. `extract_json_block` tries to find a JSON
object or array inside free-form text (useful for AI responses).
"""

from __future__ import annotations

import json
import re
from typing import Any

_FENCED_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def safe_json_loads(text: str) -> Any | None:
    """Parse JSON. Returns None on failure instead of raising."""
    if not text:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def safe_json_dumps(value: Any, *, indent: int | None = None) -> str:
    """Serialize to JSON with sensible defaults. Never raises on common types."""
    try:
        return json.dumps(value, indent=indent, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return json.dumps({"_error": "unserializable"}, ensure_ascii=False)


def _find_balanced_json(text: str, opener: str, closer: str) -> str | None:
    """Return the first balanced JSON object/array substring, respecting strings."""
    start = text.find(opener)
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def extract_json_block(text: str) -> Any | None:
    """Attempt to extract a JSON object or array from arbitrary text.

    Order of attempts:
      1. Parse the entire text as JSON.
      2. Parse the first fenced ```json ...``` block.
      3. Find the first balanced { ... } or [ ... ] block and parse it.
    """
    if not text:
        return None

    parsed = safe_json_loads(text)
    if parsed is not None:
        return parsed

    for match in _FENCED_BLOCK_RE.finditer(text):
        candidate = match.group(1).strip()
        parsed = safe_json_loads(candidate)
        if parsed is not None:
            return parsed

    for opener, closer in (("{", "}"), ("[", "]")):
        candidate = _find_balanced_json(text, opener, closer)
        if candidate:
            parsed = safe_json_loads(candidate)
            if parsed is not None:
                return parsed

    return None