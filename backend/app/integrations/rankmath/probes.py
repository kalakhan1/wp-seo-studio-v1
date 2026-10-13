"""Rank Math capability probes.

Rank Math Free does not expose a public REST API for its settings. This
module probes what is safely discoverable:

  - Whether the plugin appears to be active (via REST namespaces on /wp-json)
  - Whether a companion plugin endpoint is available (a future
    `/wp-json/wp-seo-control/v1/` namespace registered by our plugin)
  - Whether post types advertise Rank Math meta in their REST schema
    (only possible if the site has explicitly registered it)

It never attempts to read or write settings through undocumented
endpoints, and it never fabricates success.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.http_client import SafeHttpClient
from app.integrations.wordpress.types import SiteInfo

# Namespace we intend our companion plugin to register (Phase 6).
COMPANION_NAMESPACE = "wp-seo-control/v1"

# Known Rank Math REST namespaces that may appear when a site exposes them.
RANKMATH_NAMESPACES = ("rankmath/v1",)


@dataclass
class RankMathProbeResult:
    """Outcome of probing a site for Rank Math support."""

    plugin_detected: bool = False
    companion_plugin_detected: bool = False
    companion_settings_available: bool = False
    namespaces_found: list[str] = field(default_factory=list)
    reason: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)


async def probe_rankmath(
    *,
    base_url: str,
    site_info: SiteInfo | None,
    http: SafeHttpClient,
    auth_headers: dict[str, str] | None = None,
    allow_private_hosts: bool = True,
) -> RankMathProbeResult:
    """Inspect the site to determine what Rank Math integration is possible.

    Never raises on probe failure; returns a result with `reason` set.
    """
    result = RankMathProbeResult()

    if site_info is None or not site_info.namespaces:
        result.reason = "Site namespaces unavailable; cannot inspect plugins."
        return result

    result.namespaces_found = list(site_info.namespaces)

    # --- Rank Math plugin detection ----------------------------------------
    if any(ns in site_info.namespaces for ns in RANKMATH_NAMESPACES):
        result.plugin_detected = True
    else:
        # Not conclusive: many sites do not advertise plugin namespaces
        # at /wp-json even when the plugin is active.
        result.reason = (
            "Rank Math namespace not advertised. Plugin may still be active; "
            "full integration requires the companion plugin."
        )

    # --- Companion plugin detection ----------------------------------------
    if COMPANION_NAMESPACE in site_info.namespaces:
        result.companion_plugin_detected = True

    if result.companion_plugin_detected:
        # Probe the companion settings endpoint (does not require auth for a
        # simple capability probe; the plugin will return 200 with a
        # capability map, or 401/403 if not permitted).
        ok = await _probe_companion_settings(
            base_url=base_url,
            http=http,
            auth_headers=auth_headers,
            allow_private_hosts=allow_private_hosts,
        )
        result.companion_settings_available = ok
        if ok:
            result.reason = "Companion plugin detected and settings endpoint reachable."
        else:
            result.reason = (
                "Companion plugin detected but settings endpoint not reachable."
            )

    return result


async def _probe_companion_settings(
    *,
    base_url: str,
    http: SafeHttpClient,
    auth_headers: dict[str, str] | None,
    allow_private_hosts: bool,
) -> bool:
    url = f"{base_url.rstrip('/')}/wp-json/{COMPANION_NAMESPACE}/settings"
    try:
        response = await http.request(
            "GET",
            url,
            headers=auth_headers or {},
            allow_private=allow_private_hosts,
        )
    except Exception:  # noqa: BLE001 — probe must not raise
        return False
    return response.status_code == 200