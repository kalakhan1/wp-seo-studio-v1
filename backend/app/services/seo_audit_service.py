"""Technical SEO audit service.

Runs a set of independent checks. Each check:
  - Never raises. Errors become a warn/info finding with a reason.
  - Is truthful. No claim is made about external services we did not
    actually call.
  - Carries a suggested fix and an internal action path where possible.

Findings are saved to the local `audit_reports` table for history.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging import get_logger
from app.config.settings import Settings
from app.core.exceptions import AuthError, ValidationError
from app.integrations.wordpress.client import WordPressClient
from app.models.audit_report import AuditReport
from app.models.connection import Connection
from app.models.media_record import MediaRecord
from app.schemas.seo_audit import (
    AuditFinding,
    AuditHistoryItem,
    AuditHistoryResponse,
    AuditReportResponse,
    AuditSummary,
)
from app.security import secrets as secret_store

_log = get_logger(__name__)


def _make(
    check_id: str,
    label: str,
    category: str,
    severity: str,
    message: str,
    *,
    evidence: dict[str, Any] | None = None,
    suggested_fix: str = "",
    affected_urls: list[str] | None = None,
    action_path: str = "",
) -> AuditFinding:
    return AuditFinding(
        check_id=check_id,
        label=label,
        category=category,  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        message=message,
        evidence=evidence or {},
        suggested_fix=suggested_fix,
        affected_urls=affected_urls or [],
        action_path=action_path,
    )


class SEOAuditService:
    """Stateless. Construct per request with settings + session."""

    def __init__(self, *, settings: Settings, session: AsyncSession) -> None:
        self._settings = settings
        self._session = session

    # --- Run ---------------------------------------------------------------

    async def run(self, *, connection_id: int, http: Any) -> AuditReportResponse:
        connection = await self._require_connection(connection_id)
        findings: list[AuditFinding] = []
        warnings: list[str] = []

        # 1. HTTPS
        findings.append(self._check_https(connection.base_url))

        # 2. Fetch site info
        site_info: Any = None
        wp: WordPressClient | None = None
        try:
            wp = await self._wp_client(connection, http)
            site_info = await wp.get_site_info()
        except Exception as exc:  # noqa: BLE001
            warnings.append(
                f"Could not reach WordPress site info: {exc.__class__.__name__}."
            )

        # 3. Site URL consistency
        if site_info is not None:
            findings.append(self._check_site_urls(site_info))
        else:
            findings.append(
                _make(
                    "site_info.unreachable",
                    "Site info reachable",
                    "connection",
                    "warn",
                    "WordPress /wp-json was not reachable. "
                    "Other checks may be incomplete.",
                    suggested_fix="Verify the connection in Website Connection.",
                    action_path="/connection",
                )
            )

        # 4. XML sitemap
        findings.append(await self._check_sitemap(connection.base_url, http))

        # 5. robots.txt
        findings.append(await self._check_robots(connection.base_url, http))

        # 6. Permalink readability (sample post)
        findings.append(await self._check_permalink_readability(wp))

        # 7. Rank Math readiness
        findings.append(await self._check_rank_math(connection, http))

        # 8. Media alt text coverage (local cache)
        findings.append(await self._check_media_alt_text(connection.id))

        # 9. Recent post inventory
        findings.append(await self._check_post_inventory(wp))

        # 10. Empty product categories warning (best-effort)
        findings.append(await self._check_taxonomies(wp))

        summary = self._summarize(findings)
        report = AuditReportResponse(
            base_url=connection.base_url,
            discovered_at=datetime.now(timezone.utc).isoformat(),
            summary=summary,
            findings=findings,
            warnings=warnings,
        )

        # Persist to history
        try:
            record = AuditReport(
                audit_type="technical_seo",
                site_url=connection.base_url,
                summary_status=self._summary_status(summary),
                findings_json=json.dumps(
                    [f.model_dump() for f in findings],
                    ensure_ascii=False,
                ),
                notes=None,
            )
            self._session.add(record)
            await self._session.commit()
            await self._session.refresh(record)
            report.run_id = record.id
        except Exception as exc:  # noqa: BLE001
            await self._session.rollback()
            _log.warning("audit_persist_failed", error=exc.__class__.__name__)

        return report

    # --- History -----------------------------------------------------------

    async def history(
        self, *, connection_id: int | None = None, limit: int = 20
    ) -> AuditHistoryResponse:
        if connection_id is not None:
            connection = await self._require_connection(connection_id)
            stmt = (
                select(AuditReport)
                .where(AuditReport.site_url == connection.base_url)
                .order_by(AuditReport.id.desc())
                .limit(limit)
            )
        else:
            stmt = select(AuditReport).order_by(AuditReport.id.desc()).limit(limit)
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        items: list[AuditHistoryItem] = []
        for row in rows:
            try:
                findings_count = len(json.loads(row.findings_json or "[]"))
            except Exception:  # noqa: BLE001
                findings_count = 0
            items.append(
                AuditHistoryItem(
                    id=row.id,
                    site_url=row.site_url,
                    summary_status=row.summary_status,
                    created_at=row.created_at.isoformat(),
                    findings_count=findings_count,
                )
            )
        return AuditHistoryResponse(items=items)

    # --- Individual checks -------------------------------------------------

    def _check_https(self, base_url: str) -> AuditFinding:
        parsed = urlparse(base_url)
        if parsed.scheme == "https":
            return _make(
                "https.enabled",
                "HTTPS enabled",
                "connection",
                "pass",
                "The connected site uses HTTPS.",
                evidence={"base_url": base_url},
            )
        return _make(
            "https.enabled",
            "HTTPS enabled",
            "connection",
            "fail",
            "The site does not use HTTPS. Search engines treat HTTPS as a "
            "ranking signal and browsers flag non-HTTPS sites as insecure.",
            suggested_fix="Configure an SSL certificate and update the site URL.",
            action_path="/connection",
        )

    def _check_site_urls(self, site_info: Any) -> AuditFinding:
        url = (site_info.url or "").rstrip("/")
        home = (site_info.home or "").rstrip("/")
        if url and home and url != home:
            return _make(
                "site.url_home_mismatch",
                "Site URL / Home URL consistent",
                "connection",
                "warn",
                "The WordPress address and site address differ. This is "
                "valid but often indicates a subdirectory install. Verify "
                "canonical URLs are not duplicated.",
                evidence={"url": url, "home": home},
                suggested_fix="Confirm intent in WordPress → Settings → General.",
                action_path="/wordpress-settings",
            )
        return _make(
            "site.url_home_mismatch",
            "Site URL / Home URL consistent",
            "connection",
            "pass",
            "WordPress address and site address match.",
            evidence={"url": url, "home": home},
        )

    async def _check_sitemap(self, base_url: str, http: Any) -> AuditFinding:
        candidates = [
            "/sitemap_index.xml",  # Rank Math / Yoast
            "/wp-sitemap.xml",  # WordPress core
            "/sitemap.xml",
        ]
        for path in candidates:
            try:
                response = await http.request(
                    "GET",
                    f"{base_url}{path}",
                    allow_private=True,
                )
            except Exception:  # noqa: BLE001
                continue
            if response.status_code == 200 and b"<" in response.content[:200]:
                return _make(
                    "sitemap.reachable",
                    "XML sitemap reachable",
                    "sitemap",
                    "pass",
                    f"Found a sitemap at {path}.",
                    evidence={"path": path},
                )
        return _make(
            "sitemap.reachable",
            "XML sitemap reachable",
            "sitemap",
            "warn",
            "No sitemap was found at the standard locations. Search engines "
            "may take longer to discover your content.",
            suggested_fix="Enable the XML sitemap in Rank Math or install a sitemap plugin.",
            action_path="/rankmath",
        )

    async def _check_robots(self, base_url: str, http: Any) -> AuditFinding:
        try:
            response = await http.request(
                "GET",
                f"{base_url}/robots.txt",
                allow_private=True,
            )
        except Exception as exc:  # noqa: BLE001
            return _make(
                "robots.reachable",
                "robots.txt reachable",
                "robots",
                "warn",
                f"Could not fetch robots.txt ({exc.__class__.__name__}).",
            )
        if response.status_code != 200:
            return _make(
                "robots.reachable",
                "robots.txt reachable",
                "robots",
                "warn",
                f"robots.txt returned HTTP {response.status_code}.",
            )

        # Parse line by line so "disallow: /" is not confused with "allow:".
        raw_lines = [ln.strip().lower() for ln in response.text.splitlines()]
        # Skip comments
        lines = [
            ln.split("#", 1)[0].strip()
            for ln in raw_lines
            if ln and not ln.startswith("#")
        ]
        has_sitemap = any(ln.startswith("sitemap:") for ln in lines)
        has_disallow_all = any(ln == "disallow: /" for ln in lines)
        has_any_allow = any(ln.startswith("allow:") for ln in lines)

        if has_disallow_all and not has_any_allow:
            return _make(
                "robots.reachable",
                "robots.txt reachable",
                "robots",
                "fail",
                "robots.txt disallows all crawlers. Search engines will not "
                "index the site.",
                evidence={"first_200_chars": response.text[:200]},
                suggested_fix="Edit robots.txt to allow crawling.",
            )

        if has_sitemap:
            return _make(
                "robots.reachable",
                "robots.txt reachable",
                "robots",
                "pass",
                "robots.txt is present and includes a sitemap reference.",
                evidence={"has_sitemap": True},
            )

        return _make(
            "robots.reachable",
            "robots.txt reachable",
            "robots",
            "info",
            "robots.txt is present but does not reference a sitemap.",
            evidence={"has_sitemap": False},
            suggested_fix=(
                "Add a `Sitemap:` line so crawlers discover the sitemap faster."
            ),
        )

    async def _check_permalink_readability(
        self, wp: WordPressClient | None
    ) -> AuditFinding:
        if wp is None:
            return _make(
                "permalinks.readable",
                "Permalinks readable",
                "permalinks",
                "info",
                "Could not check permalinks; site info was not reachable.",
            )
        try:
            posts = await wp._get_json(  # noqa: SLF001
                "/wp-json/wp/v2/posts",
                params={"per_page": 1},
            )
        except Exception:  # noqa: BLE001
            return _make(
                "permalinks.readable",
                "Permalinks readable",
                "permalinks",
                "info",
                "No recent posts found to inspect permalinks.",
            )
        if not isinstance(posts, list) or not posts:
            return _make(
                "permalinks.readable",
                "Permalinks readable",
                "permalinks",
                "info",
                "No posts available to sample permalinks.",
            )
        link = str(posts[0].get("link", "") or "")
        if "?p=" in link or "?page_id=" in link:
            return _make(
                "permalinks.readable",
                "Permalinks readable",
                "permalinks",
                "fail",
                "Post URLs use numeric IDs. Readable permalinks help search "
                "engines and users.",
                evidence={"sample_url": link},
                suggested_fix="Set Permalinks to Post Name in WordPress.",
                action_path="/wordpress-settings",
            )
        return _make(
            "permalinks.readable",
            "Permalinks readable",
            "permalinks",
            "pass",
            "Post URLs are readable.",
            evidence={"sample_url": link},
        )

    async def _check_rank_math(
        self, connection: Connection, http: Any
    ) -> AuditFinding:
        label = connection.secret_ref or connection.label
        password = secret_store.get_secret(
            label, secret_store.FIELD_WP_APP_PASSWORD
        )
        if not password:
            return _make(
                "rankmath.available",
                "Rank Math integration available",
                "content",
                "info",
                "Stored credentials are missing. Cannot probe the companion plugin.",
            )
        from app.integrations.rankmath.client import RankMathClient
        from app.integrations.rankmath.exceptions import (
            RankMathCompanionMissingError,
            RankMathError,
        )
        from app.integrations.wordpress.auth import build_auth_headers

        try:
            auth = build_auth_headers(
                connection.auth_method, connection.username, password
            )
            rm = RankMathClient(
                base_url=connection.base_url,
                auth_headers=auth,
                http=http,
            )
            status = await rm.get_status()
        except RankMathCompanionMissingError:
            return _make(
                "rankmath.available",
                "Rank Math integration available",
                "content",
                "warn",
                "The companion plugin is not installed or not active. "
                "Per-content Rank Math fields are unavailable.",
                suggested_fix="Install the WP SEO Control Companion plugin.",
            )
        except RankMathError as exc:
            return _make(
                "rankmath.available",
                "Rank Math integration available",
                "content",
                "info",
                exc.message,
            )

        active = bool(status.get("rank_math_active", False))
        version = str(status.get("rank_math_version", "") or "")
        return _make(
            "rankmath.available",
            "Rank Math integration available",
            "content",
            "pass" if active else "warn",
            (
                f"Companion plugin present. Rank Math {version or ''} active.".strip()
                if active
                else "Companion plugin present but Rank Math is not active."
            ),
            evidence={"version": version},
        )

    async def _check_media_alt_text(self, connection_id: int) -> AuditFinding:
        result = await self._session.execute(
            select(MediaRecord).where(MediaRecord.connection_id == connection_id)
        )
        rows = result.scalars().all()
        if not rows:
            return _make(
                "media.alt_text",
                "Image alt text coverage",
                "media",
                "info",
                "No media cached locally. Upload images in Media Studio to "
                "populate this check.",
                action_path="/media-studio",
            )
        missing = [r for r in rows if not (r.alt_text or "").strip()]
        total = len(rows)
        missing_count = len(missing)
        if missing_count == 0:
            return _make(
                "media.alt_text",
                "Image alt text coverage",
                "media",
                "pass",
                f"All {total} cached image(s) have alt text.",
                evidence={"total": total},
            )
        return _make(
            "media.alt_text",
            "Image alt text coverage",
            "media",
            "warn",
            f"{missing_count} of {total} cached image(s) are missing alt text.",
            evidence={
                "total": total,
                "missing": missing_count,
                "missing_examples": [r.filename for r in missing[:5]],
            },
            suggested_fix="Add alt text in Media Studio for accessibility and image SEO.",
            action_path="/media-studio",
        )

    async def _check_post_inventory(
        self, wp: WordPressClient | None
    ) -> AuditFinding:
        if wp is None:
            return _make(
                "content.inventory",
                "Published content inventory",
                "content",
                "info",
                "Could not list posts.",
            )
        try:
            posts = await wp._get_json(  # noqa: SLF001
                "/wp-json/wp/v2/posts",
                params={"per_page": 1},
            )
        except Exception:  # noqa: BLE001
            return _make(
                "content.inventory",
                "Published content inventory",
                "content",
                "info",
                "Could not list posts.",
            )
        count = len(posts) if isinstance(posts, list) else 0
        if count == 0:
            return _make(
                "content.inventory",
                "Published content inventory",
                "content",
                "warn",
                "No published posts were returned. The site may be empty.",
                suggested_fix="Publish a few posts using the Blog Publisher.",
                action_path="/blog-publisher",
            )
        return _make(
            "content.inventory",
            "Published content inventory",
            "content",
            "pass",
            "Site returned at least one published post.",
            evidence={"sample_count": count},
        )

    async def _check_taxonomies(
        self, wp: WordPressClient | None
    ) -> AuditFinding:
        if wp is None:
            return _make(
                "structure.taxonomies",
                "Taxonomy structure",
                "structure",
                "info",
                "Could not inspect taxonomies.",
            )
        try:
            cats = await wp.list_categories()
        except Exception:  # noqa: BLE001
            return _make(
                "structure.taxonomies",
                "Taxonomy structure",
                "structure",
                "info",
                "Could not list categories.",
            )
        empty = [c for c in cats if c.count == 0]
        if not cats:
            return _make(
                "structure.taxonomies",
                "Taxonomy structure",
                "structure",
                "info",
                "No categories found.",
            )
        if empty:
            return _make(
                "structure.taxonomies",
                "Taxonomy structure",
                "structure",
                "warn",
                f"{len(empty)} of {len(cats)} categories have zero posts. "
                "Empty archives are typically not worth indexing.",
                evidence={
                    "total": len(cats),
                    "empty_count": len(empty),
                    "empty_examples": [c.name for c in empty[:5]],
                },
                suggested_fix=(
                    "Either publish posts in these categories or set them to "
                    "no-index in Rank Math."
                ),
                action_path="/rankmath",
            )
        return _make(
            "structure.taxonomies",
            "Taxonomy structure",
            "structure",
            "pass",
            f"All {len(cats)} categories have at least one post.",
            evidence={"total": len(cats)},
        )

    # --- Internals ---------------------------------------------------------

    @staticmethod
    def _summarize(findings: list[AuditFinding]) -> AuditSummary:
        summary = AuditSummary(total=len(findings))
        for f in findings:
            if f.severity == "pass":
                summary.pass_count += 1
            elif f.severity == "warn":
                summary.warn_count += 1
            elif f.severity == "fail":
                summary.fail_count += 1
            else:
                summary.info_count += 1
        return summary

    @staticmethod
    def _summary_status(summary: AuditSummary) -> str:
        if summary.fail_count > 0:
            return "errors"
        if summary.warn_count > 0:
            return "warnings"
        return "ok"

    async def _require_connection(self, connection_id: int) -> Connection:
        result = await self._session.execute(
            select(Connection).where(Connection.id == connection_id)
        )
        c = result.scalar_one_or_none()
        if c is None:
            raise ValidationError(
                "Connection not found.",
                details={"connection_id": connection_id},
            )
        return c

    async def _wp_client(self, connection: Connection, http: Any) -> WordPressClient:
        label = connection.secret_ref or connection.label
        password = secret_store.get_secret(
            label, secret_store.FIELD_WP_APP_PASSWORD
        )
        if not password:
            raise AuthError(
                "Stored WordPress credentials are missing from the OS keyring.",
                details={"label": label},
            )
        return WordPressClient(
            base_url=connection.base_url,
            username=connection.username,
            app_password=password,
            auth_method=connection.auth_method,
            http=http,
        )