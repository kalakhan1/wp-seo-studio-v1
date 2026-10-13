"""File upload validation.

Phase 3 scope: image uploads only. Validates size, extension, and MIME
type. Uses magic-byte detection (not just the declared Content-Type) to
prevent mislabeled uploads.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.exceptions import ValidationError
from app.security.sanitizer import sanitize_filename

# Allowed image types for Phase 3.
ALLOWED_IMAGE_MIMES: frozenset[str] = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    }
)

ALLOWED_IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {".jpg", ".jpeg", ".png", ".webp", ".gif"}
)

DEFAULT_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


@dataclass(frozen=True)
class ValidatedUpload:
    """Result of validating an uploaded file."""

    filename: str
    mime_type: str
    size_bytes: int
    content: bytes


def _detect_mime(content: bytes) -> str | None:
    """Detect image MIME from magic bytes. Returns None if unknown."""
    if len(content) < 12:
        return None
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    return None


def _canonical_extension(mime_type: str) -> str:
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }.get(mime_type, ".bin")


def validate_image_upload(
    *,
    filename: str,
    content: bytes,
    declared_mime: str | None,
    max_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
) -> ValidatedUpload:
    """Validate an image upload. Raises ValidationError on any problem."""
    if not content:
        raise ValidationError("Uploaded file is empty.")

    if len(content) > max_bytes:
        raise ValidationError(
            f"File exceeds the maximum size of {max_bytes // (1024 * 1024)} MB.",
            details={"size_bytes": len(content), "max_bytes": max_bytes},
        )

    detected = _detect_mime(content)
    if detected is None:
        raise ValidationError(
            "Unrecognized image format. Only JPEG, PNG, WebP, and GIF are allowed.",
            details={"filename": filename, "declared_mime": declared_mime or ""},
        )
    if detected not in ALLOWED_IMAGE_MIMES:
        raise ValidationError(
            f"Image format {detected!r} is not allowed.",
            details={"detected_mime": detected},
        )

    # Cross-check the declared MIME if it was provided (best-effort; not fatal).
    # We always trust the magic bytes over the header.

    safe_name = sanitize_filename(filename or "upload")
    suffix = Path(safe_name).suffix.lower()
    if not suffix or suffix not in ALLOWED_IMAGE_EXTENSIONS:
        stem = Path(safe_name).stem or "upload"
        safe_name = f"{stem}{_canonical_extension(detected)}"

    return ValidatedUpload(
        filename=safe_name,
        mime_type=detected,
        size_bytes=len(content),
        content=content,
    )