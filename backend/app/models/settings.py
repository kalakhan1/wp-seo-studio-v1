"""Non-secret application settings persisted in the DB.

Anything secret (passwords, tokens, API keys) stays in .env or OS keyring.
This table is for user-tweakable, non-secret preferences.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class AppSettings(Base, TimestampMixin):
    __tablename__ = "app_settings"

    # Use the setting key as the primary key
    key: Mapped[str] = mapped_column(String(200), primary_key=True)

    # Serialized value (string form). Callers know the expected type.
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Optional human-readable description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<AppSettings key={self.key!r}>"