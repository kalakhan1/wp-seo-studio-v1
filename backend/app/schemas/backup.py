"""Schemas for app-level backup and restore.

Scope: the application's own non-secret configuration:
  - Connection metadata (labels, URLs, usernames, auth method, notes)
  - Prompt templates
  - Non-secret app settings
  - Audit report summaries (optional)

NEVER included:
  - Application passwords
  - WooCommerce REST keys
  - AI API keys
  - Any secret from the OS keyring

This backup is NOT a WordPress backup. It does not include posts, pages,
products, media, or settings on the connected site.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class BackupBundle(BaseModel):
    """The complete backup payload."""

    model_config = ConfigDict(extra="allow")

    format: Literal["wp-seo-studio.backup.v1"] = "wp-seo-studio.backup.v1"
    created_at: str
    app_version: str
    connections: list[dict[str, Any]] = Field(default_factory=list)
    prompt_templates: list[dict[str, Any]] = Field(default_factory=list)
    app_settings: list[dict[str, Any]] = Field(default_factory=list)
    notes: str = ""


class BackupExportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bundle: BackupBundle
    warnings: list[str] = Field(default_factory=list)


class BackupImportRequest(BaseModel):
    """Preview or apply an import."""

    model_config = ConfigDict(extra="forbid")

    bundle: BackupBundle
    dry_run: bool = Field(
        default=True,
        description="If true, validate only. No changes are made.",
    )
    include_connections: bool = True
    include_prompt_templates: bool = True
    include_app_settings: bool = True


class BackupImportReport(BaseModel):
    """Result of a preview or actual import."""

    model_config = ConfigDict(extra="forbid")

    dry_run: bool
    connections_created: int = 0
    connections_skipped: int = 0
    prompt_templates_updated: int = 0
    app_settings_updated: int = 0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)