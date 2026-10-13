"""Locally saved drafts for products, posts, and pages.

Full payload is stored as JSON text so schema changes on the WordPress side
do not require DB migrations here. `payload_json` is authoritative for
locally saved drafts; WordPress remains authoritative for published content.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config.constants import WPObjectType
from app.db.base import Base, TimestampMixin


class Draft(Base, TimestampMixin):
    __tablename__ = "drafts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # "product" | "post" | "page" (see WPObjectType)
    object_type: Mapped[str] = mapped_column(String(40), nullable=False)

    # Optional local title for listing
    title: Mapped[str] = mapped_column(String(500), nullable=False, default="")

    # Local slug for dedup/UX
    slug: Mapped[str] = mapped_column(String(300), nullable=False, default="")

    # Optional link to a stored Connection
    connection_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # If this draft was created by editing an existing WP object
    wp_object_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Serialized form payload
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    # Optional human note
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_drafts_object_type", "object_type"),
        Index("ix_drafts_connection_id", "connection_id"),
        Index("ix_drafts_wp_object_id", "wp_object_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Draft id={self.id} type={self.object_type!r} "
            f"title={self.title!r}>"
        )


# Ensure WPObjectType is imported for type-checker awareness
_ = WPObjectType