"""Unit tests for app.security.upload_guard."""

from __future__ import annotations

import pytest

from app.core.exceptions import ValidationError
from app.security.upload_guard import (
    DEFAULT_MAX_UPLOAD_BYTES,
    validate_image_upload,
)

# Minimal valid image headers ------------------------------------------------

JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 100
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
GIF_BYTES = b"GIF89a" + b"\x00" * 100
WEBP_BYTES = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 100
PLAINTEXT_BYTES = b"hello world"


def test_validates_jpeg() -> None:
    result = validate_image_upload(
        filename="photo.jpg",
        content=JPEG_BYTES,
        declared_mime="image/jpeg",
    )
    assert result.mime_type == "image/jpeg"
    assert result.filename == "photo.jpg"
    assert result.size_bytes == len(JPEG_BYTES)


def test_validates_png() -> None:
    result = validate_image_upload(
        filename="photo.png",
        content=PNG_BYTES,
        declared_mime="image/png",
    )
    assert result.mime_type == "image/png"


def test_validates_gif() -> None:
    result = validate_image_upload(
        filename="photo.gif",
        content=GIF_BYTES,
        declared_mime="image/gif",
    )
    assert result.mime_type == "image/gif"


def test_validates_webp() -> None:
    result = validate_image_upload(
        filename="photo.webp",
        content=WEBP_BYTES,
        declared_mime="image/webp",
    )
    assert result.mime_type == "image/webp"


def test_rejects_unknown_format() -> None:
    with pytest.raises(ValidationError):
        validate_image_upload(
            filename="notes.txt",
            content=PLAINTEXT_BYTES,
            declared_mime="text/plain",
        )


def test_rejects_empty_content() -> None:
    with pytest.raises(ValidationError):
        validate_image_upload(
            filename="empty.jpg",
            content=b"",
            declared_mime="image/jpeg",
        )


def test_rejects_oversize() -> None:
    big = JPEG_BYTES + b"\x00" * (DEFAULT_MAX_UPLOAD_BYTES + 1)
    with pytest.raises(ValidationError):
        validate_image_upload(
            filename="huge.jpg",
            content=big,
            declared_mime="image/jpeg",
        )


def test_sanitizes_filename() -> None:
    result = validate_image_upload(
        filename="../../etc/passwd.jpg",
        content=JPEG_BYTES,
        declared_mime="image/jpeg",
    )
    assert "/" not in result.filename
    assert ".." not in result.filename


def test_replaces_bad_extension() -> None:
    result = validate_image_upload(
        filename="image.bin",
        content=JPEG_BYTES,
        declared_mime="image/jpeg",
    )
    assert result.filename.endswith(".jpg")


def test_magic_bytes_override_mismatched_declared_mime() -> None:
    # Declared as PNG, but bytes are JPEG.
    result = validate_image_upload(
        filename="photo.png",
        content=JPEG_BYTES,
        declared_mime="image/png",
    )
    # We trust the magic bytes: this is JPEG.
    assert result.mime_type == "image/jpeg"