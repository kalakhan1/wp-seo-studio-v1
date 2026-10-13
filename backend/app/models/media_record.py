"""Locally cached metadata for media uploaded to WordPress.

WordPress remains authoritative for the actual file. This table is a local
index so the app can list, search, and reuse media without re-querying the
site for every keystroke.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class MediaRecord(Base, TimestampMixin):
    __tablename__ = "media_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # WordPress media id, if known
    wp_media_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Original filename (post-sanitization)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)

    # Public URL returned by WordPress
    url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # MIME type
    mime: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    # File size in bytes
    size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Image dimensions (nullable for non-image media)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Alt text / title / caption / description — WordPress metadata
    alt_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # SHA-256 of the file bytes, used for local dedup
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Optional connection reference
    connection_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_media_records_wp_media_id", "wp_media_id"),
        Index("ix_media_records_filename", "filename"),
        Index("ix_media_records_content_hash", "content_hash"),
        Index("ix_media_records_connection_id", "connection_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<MediaRecord id={self.id} wp_id={self.wp_media_id} "
            f"filename={self.filename!r}>"
        )