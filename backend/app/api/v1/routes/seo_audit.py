"""Technical SEO audit endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DBSessionDep, SettingsDep
from app.core.http_client import SafeHttpClient
from app.schemas.seo_audit import (
    AuditHistoryResponse,
    AuditReportResponse,
)
from app.services.seo_audit_service import SEOAuditService

router = APIRouter(prefix="/seo-audit", tags=["seo-audit"])


def _service(settings: SettingsDep, session: DBSessionDep) -> SEOAuditService:
    return SEOAuditService(settings=settings, session=session)


@router.post(
    "/run",
    response_model=AuditReportResponse,
    summary="Run a technical SEO audit",
    description=(
        "Runs a set of independent, truthful checks and returns findings "
        "with severity, evidence, and suggested fixes. The result is also "
        "saved to local history."
    ),
)
async def run_audit(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> AuditReportResponse:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.run(connection_id=connection_id, http=http)


@router.get(
    "/history",
    response_model=AuditHistoryResponse,
    summary="List recent audits",
)
async def list_history(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> AuditHistoryResponse:
    service = _service(settings, session)
    return await service.history(connection_id=connection_id, limit=limit)