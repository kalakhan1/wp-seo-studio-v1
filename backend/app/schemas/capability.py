"""Schemas for capability discovery responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.integrations.rankmath.probes import RankMathProbeResult
from app.integrations.wordpress.types import (
    PostType,
    SiteInfo,
    Taxonomy,
    WPUser,
)


class CapabilityItem(BaseModel):
    """One discovered capability with its classification and evidence."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(
        ...,
        description="Stable machine-readable key, e.g. wp.read.post_types.",
        examples=["wp.read.post_types"],
    )
    label: str = Field(
        ...,
        description="Human-readable label.",
        examples=["Read post types"],
    )
    category: str = Field(
        ...,
        description="Category: core, woocommerce, rankmath.",
        examples=["core"],
    )
    status: str = Field(
        ...,
        description=(
            "One of: supported, read_only, requires_elevated, "
            "requires_plugin, requires_manual_setup, not_verified, unsupported."
        ),
        examples=["supported"],
    )
    method: str = Field(
        ...,
        description="HTTP method for this capability.",
        examples=["GET"],
    )
    endpoint: str = Field(
        ...,
        description="Endpoint path on the WordPress site.",
        examples=["/wp-json/wp/v2/types"],
    )
    reason: str = Field(
        default="",
        description="Explanation of the classification.",
    )
    evidence: dict[str, Any] = Field(
        default_factory=dict,
        description="Non-secret diagnostic evidence (status codes, error names).",
    )


class CapabilitySummary(BaseModel):
    """Counts of capabilities by classification."""

    model_config = ConfigDict(extra="forbid")

    supported: int = 0
    read_only: int = 0
    requires_elevated: int = 0
    requires_plugin: int = 0
    requires_manual_setup: int = 0
    not_verified: int = 0
    unsupported: int = 0


class RankMathSummary(BaseModel):
    """Flattened Rank Math probe result for the API response."""

    model_config = ConfigDict(extra="forbid")

    plugin_detected: bool = False
    companion_plugin_detected: bool = False
    companion_settings_available: bool = False
    namespaces_found: list[str] = Field(default_factory=list)
    reason: str = ""
    evidence: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_probe(cls, probe: RankMathProbeResult) -> "RankMathSummary":
        return cls(
            plugin_detected=probe.plugin_detected,
            companion_plugin_detected=probe.companion_plugin_detected,
            companion_settings_available=probe.companion_settings_available,
            namespaces_found=probe.namespaces_found,
            reason=probe.reason,
            evidence=probe.evidence,
        )


class CapabilityReport(BaseModel):
    """Complete capability discovery report."""

    model_config = ConfigDict(extra="forbid")

    base_url: str
    discovered_at: str = Field(
        ...,
        description="ISO 8601 UTC timestamp of the discovery run.",
    )
    site_info: SiteInfo | None = None
    current_user: WPUser | None = None
    post_types: list[PostType] = Field(default_factory=list)
    taxonomies: list[Taxonomy] = Field(default_factory=list)
    capabilities: list[CapabilityItem] = Field(default_factory=list)
    summary: CapabilitySummary = Field(default_factory=CapabilitySummary)
    rankmath: RankMathSummary = Field(default_factory=RankMathSummary)
    warnings: list[str] = Field(default_factory=list)