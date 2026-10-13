"""Capability discovery for a WordPress + WooCommerce site.

Performs a series of independent probes. Each probe is classified based
on what the site actually returned. Failed probes never stop the run;
they are recorded with their reason so the report is honest.

Read capabilities are verified by performing the read.
Write capabilities are inferred from the current user's WordPress
capabilities plus the presence of the endpoint — Phase 2 does not create
content.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.config.constants import CapabilityStatus
from app.core.http_client import SafeHttpClient
from app.integrations.rankmath.probes import probe_rankmath
from app.integrations.woocommerce.client import WooCommerceClient
from app.integrations.woocommerce.exceptions import (
    WooAuthError,
    WooNotFoundError,
    WooResponseError,
)
from app.integrations.wordpress.client import WordPressClient
from app.integrations.wordpress.exceptions import (
    WPAuthError,
    WPConnectionError,
    WPNotFoundError,
    WPResponseError,
)
from app.integrations.wordpress.types import (
    PostType,
    SiteInfo,
    Taxonomy,
    WPUser,
)
from app.schemas.capability import (
    CapabilityItem,
    CapabilityReport,
    CapabilitySummary,
    RankMathSummary,
)


# --- Individual probes ------------------------------------------------------


def _cap(
    key: str,
    label: str,
    category: str,
    status: CapabilityStatus,
    method: str,
    endpoint: str,
    *,
    reason: str = "",
    evidence: dict[str, Any] | None = None,
) -> CapabilityItem:
    return CapabilityItem(
        key=key,
        label=label,
        category=category,
        status=status.value,
        method=method,
        endpoint=endpoint,
        reason=reason,
        evidence=evidence or {},
    )


async def _probe_read(
    key: str,
    label: str,
    category: str,
    endpoint: str,
    runner: Any,
    *,
    elevated_hint: str = "",
) -> CapabilityItem:
    """Run a read probe and classify the outcome."""
    try:
        await runner()
    except WPAuthError as exc:
        return _cap(
            key, label, category,
            CapabilityStatus.REQUIRES_ELEVATED,
            "GET", endpoint,
            reason=elevated_hint or "Authentication failed or insufficient permissions.",
            evidence={"status": exc.details.get("status")},
        )
    except (WPNotFoundError, WPResponseError, WPConnectionError) as exc:
        return _cap(
            key, label, category,
            CapabilityStatus.NOT_VERIFIED,
            "GET", endpoint,
            reason=f"Probe failed: {exc.__class__.__name__}.",
            evidence={"error": exc.__class__.__name__},
        )
    except Exception as exc:  # noqa: BLE001 — never fail the discovery run
        return _cap(
            key, label, category,
            CapabilityStatus.NOT_VERIFIED,
            "GET", endpoint,
            reason=f"Unexpected error: {exc.__class__.__name__}.",
            evidence={"error": exc.__class__.__name__},
        )
    return _cap(
        key, label, category,
        CapabilityStatus.SUPPORTED,
        "GET", endpoint,
        reason="Read succeeded.",
    )


def _classify_write_capability(
    *,
    user: WPUser | None,
    required_caps: list[str],
    endpoint: str,
    key: str,
    label: str,
    category: str,
    method: str = "POST",
) -> CapabilityItem:
    """Classify write capability from the current user's caps."""
    if user is None:
        return _cap(
            key, label, category,
            CapabilityStatus.NOT_VERIFIED,
            method, endpoint,
            reason="Current user could not be determined.",
        )
    if not user.capabilities:
        return _cap(
            key, label, category,
            CapabilityStatus.NOT_VERIFIED,
            method, endpoint,
            reason="Capabilities were not returned for the current user.",
        )
    missing = [c for c in required_caps if not user.capabilities.get(c, False)]
    if missing:
        return _cap(
            key, label, category,
            CapabilityStatus.REQUIRES_ELEVATED,
            method, endpoint,
            reason=f"Missing required capabilities: {', '.join(missing)}.",
            evidence={"missing_capabilities": missing},
        )
    return _cap(
        key, label, category,
        CapabilityStatus.SUPPORTED,
        method, endpoint,
        reason="User has all required capabilities. Write not attempted in Phase 2.",
        evidence={"required_capabilities": required_caps},
    )


# --- WooCommerce probes -----------------------------------------------------


async def _probe_woocommerce(
    wc_client: WooCommerceClient | None,
) -> tuple[list[CapabilityItem], list[str]]:
    """Probe WooCommerce endpoints. Returns items + warnings."""
    items: list[CapabilityItem] = []
    warnings: list[str] = []

    if wc_client is None:
        return (
            [
                _cap(
                    "wc.read.products", "Read products", "woocommerce",
                    CapabilityStatus.REQUIRES_MANUAL_SETUP,
                    "GET", "/wp-json/wc/v3/products",
                    reason="WooCommerce REST credentials were not provided.",
                ),
                _cap(
                    "wc.read.orders", "Read orders", "woocommerce",
                    CapabilityStatus.REQUIRES_MANUAL_SETUP,
                    "GET", "/wp-json/wc/v3/orders",
                    reason="WooCommerce REST credentials were not provided.",
                ),
                _cap(
                    "wc.read.payment_gateways", "Read payment gateways", "woocommerce",
                    CapabilityStatus.REQUIRES_MANUAL_SETUP,
                    "GET", "/wp-json/wc/v3/payment_gateways",
                    reason="WooCommerce REST credentials were not provided.",
                ),
                _cap(
                    "wc.read.shipping_zones", "Read shipping zones", "woocommerce",
                    CapabilityStatus.REQUIRES_MANUAL_SETUP,
                    "GET", "/wp-json/wc/v3/shipping/zones",
                    reason="WooCommerce REST credentials were not provided.",
                ),
            ],
            warnings,
        )

    # Products
    items.append(
        await _probe_wc_endpoint(
            key="wc.read.products",
            label="Read products",
            endpoint="/wp-json/wc/v3/products",
            runner=wc_client.list_products,
        )
    )
    # Payment gateways
    items.append(
        await _probe_wc_endpoint(
            key="wc.read.payment_gateways",
            label="Read payment gateways (COD)",
            endpoint="/wp-json/wc/v3/payment_gateways",
            runner=wc_client.list_payment_gateways,
        )
    )
    # Shipping zones
    items.append(
        await _probe_wc_endpoint(
            key="wc.read.shipping_zones",
            label="Read shipping zones",
            endpoint="/wp-json/wc/v3/shipping/zones",
            runner=wc_client.list_shipping_zones,
        )
    )

    return items, warnings


async def _probe_wc_endpoint(
    *,
    key: str,
    label: str,
    endpoint: str,
    runner: Any,
) -> CapabilityItem:
    try:
        await runner()
    except WooNotFoundError:
        return _cap(
            key, label, "woocommerce",
            CapabilityStatus.UNSUPPORTED,
            "GET", endpoint,
            reason="WooCommerce endpoint not found. Is WooCommerce installed and active?",
        )
    except WooAuthError as exc:
        return _cap(
            key, label, "woocommerce",
            CapabilityStatus.REQUIRES_MANUAL_SETUP,
            "GET", endpoint,
            reason="WooCommerce REST authentication failed. Generate REST API keys in WooCommerce → Settings → Advanced → REST API.",
            evidence={"status": exc.details.get("status")},
        )
    except (WooResponseError, Exception) as exc:  # noqa: BLE001
        return _cap(
            key, label, "woocommerce",
            CapabilityStatus.NOT_VERIFIED,
            "GET", endpoint,
            reason=f"Probe failed: {exc.__class__.__name__}.",
            evidence={"error": exc.__class__.__name__},
        )
    return _cap(
        key, label, "woocommerce",
        CapabilityStatus.SUPPORTED,
        "GET", endpoint,
        reason="WooCommerce read succeeded.",
    )


# --- Aggregation ------------------------------------------------------------


def _summarize(items: list[CapabilityItem]) -> CapabilitySummary:
    summary = CapabilitySummary()
    for item in items:
        if item.status == CapabilityStatus.SUPPORTED.value:
            summary.supported += 1
        elif item.status == CapabilityStatus.READ_ONLY.value:
            summary.read_only += 1
        elif item.status == CapabilityStatus.REQUIRES_ELEVATED.value:
            summary.requires_elevated += 1
        elif item.status == CapabilityStatus.REQUIRES_PLUGIN.value:
            summary.requires_plugin += 1
        elif item.status == CapabilityStatus.REQUIRES_MANUAL_SETUP.value:
            summary.requires_manual_setup += 1
        elif item.status == CapabilityStatus.NOT_VERIFIED.value:
            summary.not_verified += 1
        elif item.status == CapabilityStatus.UNSUPPORTED.value:
            summary.unsupported += 1
    return summary


# --- Public entry point -----------------------------------------------------


async def discover_capabilities(
    *,
    base_url: str,
    wp_client: WordPressClient,
    http: SafeHttpClient,
    wc_client: WooCommerceClient | None = None,
    auth_headers: dict[str, str] | None = None,
    allow_private_hosts: bool = True,
) -> CapabilityReport:
    """Run capability discovery. Never raises for probe failures."""
    warnings: list[str] = []
    items: list[CapabilityItem] = []

    # --- Site info (no auth) ----------------------------------------------
    site_info: SiteInfo | None = None
    try:
        site_info = await wp_client.get_site_info()
        items.append(
            _cap(
                "wp.read.site_info", "Read site information", "core",
                CapabilityStatus.SUPPORTED,
                "GET", "/wp-json",
                reason="Public endpoint responded.",
            )
        )
    except Exception as exc:  # noqa: BLE001
        items.append(
            _cap(
                "wp.read.site_info", "Read site information", "core",
                CapabilityStatus.NOT_VERIFIED,
                "GET", "/wp-json",
                reason=f"Probe failed: {exc.__class__.__name__}.",
                evidence={"error": exc.__class__.__name__},
            )
        )
        warnings.append("Could not read site information from /wp-json.")

    # --- Current user (auth required) -------------------------------------
    current_user: WPUser | None = None
    try:
        current_user = await wp_client.get_current_user()
        items.append(
            _cap(
                "wp.read.current_user", "Read current user", "core",
                CapabilityStatus.SUPPORTED,
                "GET", "/wp-json/wp/v2/users/me",
                reason="Authenticated read succeeded.",
            )
        )
    except WPAuthError as exc:
        items.append(
            _cap(
                "wp.read.current_user", "Read current user", "core",
                CapabilityStatus.REQUIRES_ELEVATED,
                "GET", "/wp-json/wp/v2/users/me",
                reason="Authentication failed or permission denied.",
                evidence={"status": exc.details.get("status")},
            )
        )
        warnings.append(
            "Could not authenticate. Verify username and application password."
        )
    except Exception as exc:  # noqa: BLE001
        items.append(
            _cap(
                "wp.read.current_user", "Read current user", "core",
                CapabilityStatus.NOT_VERIFIED,
                "GET", "/wp-json/wp/v2/users/me",
                reason=f"Probe failed: {exc.__class__.__name__}.",
                evidence={"error": exc.__class__.__name__},
            )
        )

    # --- Post types --------------------------------------------------------
    post_types: list[PostType] = []
    items.append(
        await _probe_read(
            "wp.read.post_types", "Read post types", "core",
            "/wp-json/wp/v2/types",
            wp_client.list_post_types,
        )
    )
    try:
        post_types = await wp_client.list_post_types()
    except Exception:  # noqa: BLE001
        post_types = []

    # --- Taxonomies --------------------------------------------------------
    taxonomies: list[Taxonomy] = []
    items.append(
        await _probe_read(
            "wp.read.taxonomies", "Read taxonomies", "core",
            "/wp-json/wp/v2/taxonomies",
            wp_client.list_taxonomies,
        )
    )
    try:
        taxonomies = await wp_client.list_taxonomies()
    except Exception:  # noqa: BLE001
        taxonomies = []

    # --- Media list --------------------------------------------------------
    items.append(
        await _probe_read(
            "wp.read.media", "Read media library", "core",
            "/wp-json/wp/v2/media",
            wp_client.list_media,
        )
    )

    # --- Write capabilities (classified, not performed) -------------------
    items.append(
        _classify_write_capability(
            user=current_user,
            required_caps=["edit_posts", "publish_posts"],
            endpoint="/wp-json/wp/v2/posts",
            key="wp.write.posts",
            label="Create or update posts",
            category="core",
        )
    )
    items.append(
        _classify_write_capability(
            user=current_user,
            required_caps=["edit_pages", "publish_pages"],
            endpoint="/wp-json/wp/v2/pages",
            key="wp.write.pages",
            label="Create or update pages",
            category="core",
        )
    )
    items.append(
        _classify_write_capability(
            user=current_user,
            required_caps=["upload_files"],
            endpoint="/wp-json/wp/v2/media",
            key="wp.write.media",
            label="Upload media",
            category="core",
        )
    )
    items.append(
        _classify_write_capability(
            user=current_user,
            required_caps=["manage_categories"],
            endpoint="/wp-json/wp/v2/categories",
            key="wp.write.categories",
            label="Manage categories",
            category="core",
        )
    )

    # --- WooCommerce -------------------------------------------------------
    wc_items, wc_warnings = await _probe_woocommerce(wc_client)
    items.extend(wc_items)
    warnings.extend(wc_warnings)

    # --- Rank Math ---------------------------------------------------------
    rm_probe = await probe_rankmath(
        base_url=base_url,
        site_info=site_info,
        http=http,
        auth_headers=auth_headers,
        allow_private_hosts=allow_private_hosts,
    )

    if not rm_probe.companion_plugin_detected:
        items.append(
            _cap(
                "rankmath.read.settings", "Read Rank Math settings", "rankmath",
                CapabilityStatus.REQUIRES_PLUGIN,
                "GET", "/wp-json/wp-seo-control/v1/settings",
                reason="Companion plugin not detected. Rank Math settings are not exposed via standard REST.",
            )
        )
        items.append(
            _cap(
                "rankmath.write.meta", "Write Rank Math post meta", "rankmath",
                CapabilityStatus.REQUIRES_PLUGIN,
                "POST", "/wp-json/wp-seo-control/v1/meta",
                reason="Companion plugin not detected. Rank Math meta is not exposed via standard REST.",
            )
        )
    else:
        items.append(
            _cap(
                "rankmath.read.settings", "Read Rank Math settings", "rankmath",
                CapabilityStatus.SUPPORTED if rm_probe.companion_settings_available
                else CapabilityStatus.REQUIRES_ELEVATED,
                "GET", "/wp-json/wp-seo-control/v1/settings",
                reason=(
                    "Companion plugin present and settings reachable."
                    if rm_probe.companion_settings_available
                    else "Companion plugin present but settings endpoint not reachable."
                ),
            )
        )
        items.append(
            _cap(
                "rankmath.write.meta", "Write Rank Math post meta", "rankmath",
                CapabilityStatus.SUPPORTED if rm_probe.companion_settings_available
                else CapabilityStatus.REQUIRES_ELEVATED,
                "POST", "/wp-json/wp-seo-control/v1/meta",
                reason="Companion plugin present.",
            )
        )

    summary = _summarize(items)

    return CapabilityReport(
        base_url=base_url,
        discovered_at=datetime.now(timezone.utc).isoformat(),
        site_info=site_info,
        current_user=current_user,
        post_types=post_types,
        taxonomies=taxonomies,
        capabilities=items,
        summary=summary,
        rankmath=RankMathSummary.from_probe(rm_probe),
        warnings=warnings,
    )