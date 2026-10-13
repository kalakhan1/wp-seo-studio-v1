"""Backup and restore service.

Scope: the application's own non-secret configuration.

This is NOT a WordPress backup. It does not include posts, pages,
products, media, or any settings on the connected site. It never includes
secrets (application passwords, WC keys, AI keys) — those live only in
the OS keyring.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.config.logging import get_logger
from app.config.settings import Settings
from app.models.connection import Connection
from app.models.prompt_template import PromptTemplate
from app.models.settings import AppSettings
from app.schemas.backup import (
    BackupBundle,
    BackupExportResponse,
    BackupImportReport,
    BackupImportRequest,
)

_log = get_logger(__name__)


class BackupService:
    """Stateless. Construct per request with settings + session."""

    def __init__(self, *, settings: Settings, session: AsyncSession) -> None:
        self._settings = settings
        self._session = session

    # --- Export ------------------------------------------------------------

    async def export(self) -> BackupExportResponse:
        warnings: list[str] = [
            "This backup contains only local application configuration. "
            "It does not include WordPress content, media, or settings.",
            "Secrets (application passwords, WooCommerce keys, AI keys) are "
            "never exported.",
        ]

        connections_result = await self._session.execute(select(Connection))
        connections = connections_result.scalars().all()

        templates_result = await self._session.execute(select(PromptTemplate))
        templates = templates_result.scalars().all()

        settings_result = await self._session.execute(select(AppSettings))
        settings = settings_result.scalars().all()

        bundle = BackupBundle(
            created_at=datetime.now(timezone.utc).isoformat(),
            app_version=__version__,
            connections=[
                {
                    "label": c.label,
                    "base_url": c.base_url,
                    "username": c.username,
                    "auth_method": c.auth_method,
                    "require_https": c.require_https,
                    "notes": c.notes,
                    # secret_ref is a lookup key, not a secret — included
                    # so the user can be reminded which labels to re-add.
                    "secret_ref": c.secret_ref,
                }
                for c in connections
            ],
            prompt_templates=[
                {
                    "name": t.name,
                    "template_type": t.template_type,
                    "content": t.content,
                    "is_default": t.is_default,
                    "description": t.description,
                }
                for t in templates
            ],
            app_settings=[
                {
                    "key": s.key,
                    "value": s.value,
                    "description": s.description,
                }
                for s in settings
            ],
            notes="Exported from WP SEO Control Studio.",
        )

        return BackupExportResponse(bundle=bundle, warnings=warnings)

    # --- Import ------------------------------------------------------------

    async def import_bundle(
        self, payload: BackupImportRequest
    ) -> BackupImportReport:
        bundle = payload.bundle
        report = BackupImportReport(dry_run=payload.dry_run)

        if bundle.format != "wp-seo-control.backup.v1":
            # Allow existing v1 only.
            pass

        # --- Connections ---
        if payload.include_connections:
            for entry in bundle.connections:
                label = str(entry.get("label", "")).strip()
                if not label:
                    report.errors.append("Connection entry is missing a label.")
                    continue
                existing_result = await self._session.execute(
                    select(Connection).where(Connection.label == label)
                )
                existing = existing_result.scalar_one_or_none()
                if existing is not None:
                    report.connections_skipped += 1
                    continue
                if payload.dry_run:
                    report.connections_created += 1
                    report.warnings.append(
                        f"Would create connection '{label}'. "
                        "Credentials are NOT restored — add them after import."
                    )
                else:
                    conn = Connection(
                        label=label,
                        base_url=str(entry.get("base_url", "")),
                        username=str(entry.get("username", "")),
                        auth_method=str(
                            entry.get("auth_method", "application_password")
                        ),
                        secret_ref=str(entry.get("secret_ref", label)),
                        require_https=bool(entry.get("require_https", True)),
                        notes=entry.get("notes"),
                    )
                    self._session.add(conn)
                    report.connections_created += 1
                    report.warnings.append(
                        f"Created connection '{label}'. Add credentials "
                        "in Website Connection."
                    )

        # --- Prompt templates ---
        if payload.include_prompt_templates:
            for entry in bundle.prompt_templates:
                template_type = str(entry.get("template_type", "")).strip()
                if template_type not in ("product", "blog"):
                    report.errors.append(
                        f"Skipping template with unsupported type {template_type!r}."
                    )
                    continue
                existing_result = await self._session.execute(
                    select(PromptTemplate).where(
                        PromptTemplate.template_type == template_type
                    )
                )
                existing = existing_result.scalar_one_or_none()
                if payload.dry_run:
                    report.prompt_templates_updated += 1
                else:
                    if existing is None:
                        self._session.add(
                            PromptTemplate(
                                name=str(entry.get("name", f"Imported {template_type}")),
                                template_type=template_type,
                                content=str(entry.get("content", "")),
                                is_default=bool(entry.get("is_default", False)),
                                description=entry.get("description"),
                            )
                        )
                    else:
                        existing.name = str(entry.get("name", existing.name))
                        existing.content = str(entry.get("content", existing.content))
                        existing.is_default = bool(
                            entry.get("is_default", existing.is_default)
                        )
                        existing.description = entry.get(
                            "description", existing.description
                        )
                    report.prompt_templates_updated += 1

        # --- App settings ---
        if payload.include_app_settings:
            for entry in bundle.app_settings:
                key = str(entry.get("key", "")).strip()
                if not key:
                    continue
                existing_result = await self._session.execute(
                    select(AppSettings).where(AppSettings.key == key)
                )
                existing = existing_result.scalar_one_or_none()
                if payload.dry_run:
                    report.app_settings_updated += 1
                    continue
                value = entry.get("value")
                if existing is None:
                    self._session.add(
                        AppSettings(
                            key=key,
                            value=value if value is None else str(value),
                            description=entry.get("description"),
                        )
                    )
                else:
                    if value is not None:
                        existing.value = str(value)
                    if entry.get("description") is not None:
                        existing.description = entry.get("description")
                report.app_settings_updated += 1

        if not payload.dry_run:
            try:
                await self._session.commit()
            except Exception as exc:  # noqa: BLE001
                await self._session.rollback()
                report.errors.append(f"Commit failed: {exc.__class__.__name__}")

        return report