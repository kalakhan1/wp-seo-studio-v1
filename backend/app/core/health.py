"""Health check aggregation.

Phase 1 checks:
  - settings load
  - SQLite database reachable
  - mock mode status
  - overall status

Future phases will add WordPress/WooCommerce/Rank Math reachability checks.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app import __version__
from app.config.settings import Settings


@dataclass
class ComponentHealth:
    name: str
    status: str  # "ok" | "degraded" | "failed"
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HealthReport:
    status: str
    mode: str
    version: str
    timestamp: str
    components: list[ComponentHealth] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "mode": self.mode,
            "version": self.version,
            "timestamp": self.timestamp,
            "components": [c.to_dict() for c in self.components],
        }


async def check_database(engine: AsyncEngine) -> ComponentHealth:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return ComponentHealth(name="database", status="ok", detail="reachable")
    except Exception as exc:  # noqa: BLE001 - health check must never raise
        return ComponentHealth(
            name="database",
            status="failed",
            detail=f"{exc.__class__.__name__}: {exc}",
        )


def check_settings(settings: Settings) -> ComponentHealth:
    try:
        # Force evaluation of derived properties.
        _ = settings.effective_app_mode
        _ = settings.is_production
        return ComponentHealth(name="settings", status="ok", detail="loaded")
    except Exception as exc:  # noqa: BLE001
        return ComponentHealth(
            name="settings",
            status="failed",
            detail=f"{exc.__class__.__name__}: {exc}",
        )


def check_mode(settings: Settings) -> ComponentHealth:
    mode = settings.effective_app_mode.value
    detail = "mock mode: no external calls" if mode == "mock" else "real mode: external calls enabled"
    return ComponentHealth(name="mode", status="ok", detail=detail)


def _overall_status(components: list[ComponentHealth]) -> str:
    if any(c.status == "failed" for c in components):
        return "failed"
    if any(c.status == "degraded" for c in components):
        return "degraded"
    return "ok"


async def build_health_report(
    settings: Settings,
    engine: AsyncEngine | None = None,
) -> HealthReport:
    components: list[ComponentHealth] = [
        check_settings(settings),
        check_mode(settings),
    ]
    if engine is not None:
        components.append(await check_database(engine))

    return HealthReport(
        status=_overall_status(components),
        mode=settings.effective_app_mode.value,
        version=__version__,
        timestamp=datetime.now(timezone.utc).isoformat(),
        components=components,
    )