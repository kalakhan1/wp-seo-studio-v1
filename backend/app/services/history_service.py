"""Publishing history service.

Read-only view of the local `publish_history` table.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.models.publish_history import PublishHistory
from app.schemas.history import (
    HistoryEntry,
    HistoryListResponse,
    HistorySummary,
)


class HistoryService:
    """Stateless. Construct per request with settings + session."""

    def __init__(self, *, settings: Settings, session: AsyncSession) -> None:
        self._settings = settings
        self._session = session

    async def list_entries(
        self,
        *,
        object_type: str | None = None,
        status: str | None = None,
        connection_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> HistoryListResponse:
        stmt = select(PublishHistory)
        count_stmt = select(func.count(PublishHistory.id))

        if object_type:
            stmt = stmt.where(PublishHistory.object_type == object_type)
            count_stmt = count_stmt.where(
                PublishHistory.object_type == object_type
            )
        if status:
            stmt = stmt.where(PublishHistory.status == status)
            count_stmt = count_stmt.where(PublishHistory.status == status)
        if connection_id is not None:
            stmt = stmt.where(PublishHistory.connection_id == connection_id)
            count_stmt = count_stmt.where(
                PublishHistory.connection_id == connection_id
            )

        stmt = stmt.order_by(PublishHistory.id.desc()).limit(limit).offset(offset)

        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        total_result = await self._session.execute(count_stmt)
        total = int(total_result.scalar_one() or 0)

        return HistoryListResponse(
            items=[self._to_entry(r) for r in rows],
            total=total,
        )

    async def summary(self) -> HistorySummary:
        result = await self._session.execute(
            select(PublishHistory.status, func.count(PublishHistory.id)).group_by(
                PublishHistory.status
            )
        )
        rows = result.all()
        summary = HistorySummary()
        for status, count in rows:
            c = int(count)
            summary.total += c
            if status == "success":
                summary.success = c
            elif status == "failed":
                summary.failed = c
            elif status == "partial":
                summary.partial = c
        return summary

    @staticmethod
    def _to_entry(row: PublishHistory) -> HistoryEntry:
        return HistoryEntry(
            id=row.id,
            object_type=row.object_type,
            operation=row.operation,
            status=row.status,
            wp_object_id=row.wp_object_id,
            permalink=row.permalink,
            message=row.message,
            idempotency_key=row.idempotency_key,
            connection_id=row.connection_id,
            created_at=row.created_at.isoformat(),
        )