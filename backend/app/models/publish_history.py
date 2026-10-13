"""Audit history of publish/update operations against WordPress.

Only sanitized error messages are stored here. Secrets never appear in this
table, even accidentally.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class PublishHistory(Base, TimestampMixin):
    __tablename__ = "publish_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # "post" | "page" | "product" | "media" | "settings" (free-form)
    object_type: Mapped[str] = mapped_column(String(40), nullable=False)

    # WordPress object id returned by the API (nullable if operation failed)
    wp_object_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Final permalink returned by WordPress, if any
    permalink: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # "create" | "update" | "delete" | "publish" | "schedule" | "upload"
    operation: Mapped[str] = mapped_column(String(40), nullable=False)

    # "success" | "failed" | "partial"
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    # Sanitized human-readable message (no secrets)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Deterministic idempotency key, if this op was deduped
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Optional connection reference
    connection_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Optional request id for correlation with logs
    request_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        Index("ix_publish_history_object_type", "object_type"),
        Index("ix_publish_history_wp_object_id", "wp_object_id"),
        Index("ix_publish_history_status", "status"),
        Index("ix_publish_history_idempotency_key", "idempotency_key"),
    )

    def __repr__(self) -> str:
        return (
            f"<PublishHistory id={self.id} op={self.operation!r} "
            f"status={self.status!r} wp_id={self.wp_object_id}>"
        )