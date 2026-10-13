"""Editable AI prompt templates (product / blog / page)."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class PromptTemplate(Base, TimestampMixin):
    __tablename__ = "prompt_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Human-readable name, e.g. "Default Product Prompt"
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # "product" | "blog" | "page"
    template_type: Mapped[str] = mapped_column(String(40), nullable=False)

    # Template body (text). Supports placeholders in a documented syntax.
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # True if this is the shipped default for its type
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Optional short description for the UI
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_prompt_templates_template_type", "template_type"),
        Index("ix_prompt_templates_is_default", "is_default"),
    )

    def __repr__(self) -> str:
        return (
            f"<PromptTemplate id={self.id} type={self.template_type!r} "
            f"name={self.name!r} default={self.is_default}>"
        )