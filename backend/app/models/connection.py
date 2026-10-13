"""Stored WordPress connection profiles.

Secrets are NEVER stored here. Credentials live in .env or the OS keyring;
this table only holds non-secret metadata plus a stable reference key that
maps to a secret entry elsewhere.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config.constants import AuthMethod
from app.db.base import Base, TimestampMixin


class Connection(Base, TimestampMixin):
    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Human label, e.g. "Production Store", "Staging"
    label: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)

    # WordPress base URL, no trailing slash
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)

    # WordPress username for Application Passwords / Basic
    username: Mapped[str] = mapped_column(String(200), nullable=False, default="")

    # Authentication method (see AuthMethod enum)
    auth_method: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=AuthMethod.APPLICATION_PASSWORD.value,
    )

    # Key name used to look up the secret from env/keyring.
    # Example: "WP_APP_PASSWORD_PROD". Never the secret itself.
    secret_ref: Mapped[str] = mapped_column(String(200), nullable=False, default="")

    # Whether HTTPS is required for this profile
    require_https: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Free-form notes (no secrets)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps of last connection verification
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_verified_ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return f"<Connection id={self.id} label={self.label!r} base_url={self.base_url!r}>"