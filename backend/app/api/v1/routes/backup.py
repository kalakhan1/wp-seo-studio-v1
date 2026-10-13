"""Backup and restore endpoints.

Scope is limited to the application's non-secret configuration.
This is not a WordPress backup.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DBSessionDep, SettingsDep
from app.schemas.backup import (
    BackupExportResponse,
    BackupImportReport,
    BackupImportRequest,
)
from app.services.backup_service import BackupService

router = APIRouter(prefix="/backup", tags=["backup"])


def _service(settings: SettingsDep, session: DBSessionDep) -> BackupService:
    return BackupService(settings=settings, session=session)


@router.get(
    "/export",
    response_model=BackupExportResponse,
    summary="Export app configuration (no secrets)",
    description=(
        "Exports connection metadata, prompt templates, and non-secret "
        "app settings. Never includes application passwords, WooCommerce "
        "keys, or AI keys. Not a WordPress backup."
    ),
)
async def export_backup(
    settings: SettingsDep,
    session: DBSessionDep,
) -> BackupExportResponse:
    return await _service(settings, session).export()


@router.post(
    "/import",
    response_model=BackupImportReport,
    summary="Preview or apply an import",
    description=(
        "Set dry_run=true to validate without changes. Import never "
        "restores secrets. Connections are created without credentials; "
        "the user must add credentials afterward."
    ),
)
async def import_backup(
    payload: BackupImportRequest,
    settings: SettingsDep,
    session: DBSessionDep,
) -> BackupImportReport:
    return await _service(settings, session).import_bundle(payload)