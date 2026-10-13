"""Stored technical SEO audit reports."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class AuditReport(Base, TimestampMixin):
    __tablename__ = "audit_reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # "technical_seo" | "content" | "media" (free-form)
    audit_type: Mapped[str] = mapped_column(String(60), nullable=False)

    # Site the audit was run against
    site_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")

    # Overall rollup: "ok" | "warnings" | "errors"
    summary_status: Mapped[str] = mapped_column(String(20), nullable=False, default="ok")

    # Serialized list of findings
    findings_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    # Optional notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_audit_reports_audit_type", "audit_type"),
        Index("ix_audit_reports_site_url", "site_url"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditReport id={self.id} type={self.audit_type!r} "
            f"status={self.summary_status!r}>"
        )