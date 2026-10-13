"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncEngine

from app.api.deps import SettingsDep
from app.core.health import build_health_report
from app.db.session import get_engine
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


def _get_engine() -> AsyncEngine:
    return get_engine()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description=(
        "Returns the current status of the application. Safe to call "
        "without authentication. Never exposes secrets."
    ),
)
async def health(
    settings: SettingsDep,
) -> HealthResponse:
    engine = _get_engine()
    report = await build_health_report(settings, engine=engine)
    return HealthResponse(**report.to_dict())