"""Schemas for the technical SEO audit.

Findings are truthful: every finding carries a severity, evidence, and —
when possible — a suggested fix and a link to the relevant section of
the studio. The audit never claims external facts (Search Console
verification, ranking position, Merchant Center approval) unless a
service is actually connected.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


Severity = Literal["info", "pass", "warn", "fail"]
CheckCategory = Literal[
    "connection",
    "permalinks",
    "sitemap",
    "robots",
    "indexability",
    "content",
    "media",
    "structure",
    "performance",
]


class AuditFinding(BaseModel):
    """A single finding from the audit."""

    model_config = ConfigDict(extra="forbid")

    check_id: str = Field(
        ...,
        description="Stable check identifier.",
        examples=["https.enabled"],
    )
    label: str = Field(..., examples=["HTTPS enabled"])
    category: CheckCategory
    severity: Severity
    message: str = Field(..., description="Human-readable summary.")
    evidence: dict[str, Any] = Field(default_factory=dict)
    suggested_fix: str = ""
    affected_urls: list[str] = Field(default_factory=list)
    action_path: str = Field(
        default="",
        description="Internal app route where the user can act on this finding.",
        examples=["/wordpress-settings"],
    )


class AuditSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pass_count: int = 0
    warn_count: int = 0
    fail_count: int = 0
    info_count: int = 0
    total: int = 0


class AuditReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_url: str
    discovered_at: str
    summary: AuditSummary
    findings: list[AuditFinding] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    run_id: int | None = Field(
        default=None,
        description="Local audit_reports row id, if persisted.",
    )


class AuditHistoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    site_url: str
    summary_status: str
    created_at: str
    findings_count: int


class AuditHistoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AuditHistoryItem] = Field(default_factory=list)