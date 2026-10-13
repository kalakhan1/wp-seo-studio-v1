"""DB integration tests: engine, session, metadata creation."""

from __future__ import annotations

from sqlalchemy import text

from app.db.base import Base
from app.db.session import dispose_engine, get_engine, init_engine
from app.models import (
    AppSettings,
    AuditReport,
    Connection,
    Draft,
    JobLog,
    MediaRecord,
    PromptTemplate,
    PublishHistory,
)


async def test_metadata_contains_all_phase1_tables() -> None:
    expected_tables = {
        "connections",
        "drafts",
        "publish_history",
        "audit_reports",
        "prompt_templates",
        "media_records",
        "job_logs",
        "app_settings",
    }
    assert expected_tables.issubset(set(Base.metadata.tables.keys()))


async def test_models_are_importable() -> None:
    # Just referencing them is enough to catch import errors.
    assert Connection.__tablename__ == "connections"
    assert Draft.__tablename__ == "drafts"
    assert PublishHistory.__tablename__ == "publish_history"
    assert AuditReport.__tablename__ == "audit_reports"
    assert PromptTemplate.__tablename__ == "prompt_templates"
    assert MediaRecord.__tablename__ == "media_records"
    assert JobLog.__tablename__ == "job_logs"
    assert AppSettings.__tablename__ == "app_settings"


async def test_engine_can_execute_select(test_settings) -> None:  # type: ignore[no-untyped-def]
    await dispose_engine()
    engine = init_engine(test_settings)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    finally:
        await dispose_engine()