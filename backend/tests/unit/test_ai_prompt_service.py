"""Unit tests for AIPromptService."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config.settings import Settings
from app.core.exceptions import ValidationError
from app.db.base import Base
from app.db.session import dispose_engine, init_engine
from app.models.prompt_template import PromptTemplate
from app.services.ai_prompt_service import AIPromptService


def _settings(tmp_path) -> Settings:  # type: ignore[no-untyped-def]
    return Settings(
        app_env="development",
        app_mode="mock",
        log_level="warning",
        http_timeout=5,
        http_max_retries=0,
        http_max_response_bytes=5_000_000,
        db_url=f"sqlite+aiosqlite:///{tmp_path / 'ai.db'}",
        ai_provider="none",
    )


@pytest.fixture
async def db_session(tmp_path) -> AsyncIterator[AsyncSession]:  # type: ignore[no-untyped-def]
    settings = _settings(tmp_path)
    await dispose_engine()
    engine = init_engine(settings)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await dispose_engine()


@pytest.fixture
def settings_for_service(tmp_path) -> Settings:  # type: ignore[no-untyped-def]
    return _settings(tmp_path)


async def test_list_templates_seeds_defaults(
    db_session: AsyncSession,
    settings_for_service: Settings,
) -> None:
    service = AIPromptService(
        settings=settings_for_service, session=db_session
    )
    result = await service.list_templates()
    assert len(result.items) == 2
    types = {t.template_type for t in result.items}
    assert types == {"product", "blog"}


async def test_ensure_defaults_is_idempotent(
    db_session: AsyncSession,
    settings_for_service: Settings,
) -> None:
    service = AIPromptService(
        settings=settings_for_service, session=db_session
    )
    await service.list_templates()
    await service.list_templates()
    result = await db_session.execute(select(PromptTemplate))
    rows = result.scalars().all()
    assert len(rows) == 2


async def test_update_and_restore_template(
    db_session: AsyncSession,
    settings_for_service: Settings,
) -> None:
    service = AIPromptService(
        settings=settings_for_service, session=db_session
    )
    await service.list_templates()

    updated = await service.update_template("blog", "Custom template body")
    assert updated.content == "Custom template body"
    assert updated.is_default is False

    restored = await service.restore_default("blog")
    assert restored.restored is True
    assert restored.template.is_default is True
    assert "blog article" in restored.template.content.lower()


async def test_get_unknown_template_raises(
    db_session: AsyncSession,
    settings_for_service: Settings,
) -> None:
    service = AIPromptService(
        settings=settings_for_service, session=db_session
    )
    with pytest.raises(ValidationError):
        await service._default_for("unknown")  # noqa: SLF001


async def test_status_reports_mock_provider(
    db_session: AsyncSession,
    settings_for_service: Settings,
) -> None:
    service = AIPromptService(
        settings=settings_for_service, session=db_session
    )
    status = await service.status()
    assert status.available is True
    assert status.provider in ("mock", "none")


async def test_generate_returns_parsed_json(
    db_session: AsyncSession,
    settings_for_service: Settings,
) -> None:
    service = AIPromptService(
        settings=settings_for_service, session=db_session
    )
    result = await service.generate(
        prompt="Write a product for test",
        template_type="product",
    )
    assert result.ok is True
    assert result.provider == "mock"
    assert result.parsed is not None
    assert isinstance(result.parsed, dict)
    assert "product_name" in result.parsed


async def test_generate_blog_returns_blog_shape(
    db_session: AsyncSession,
    settings_for_service: Settings,
) -> None:
    service = AIPromptService(
        settings=settings_for_service, session=db_session
    )
    result = await service.generate(
        prompt="Write a blog post",
        template_type="blog",
    )
    assert result.ok is True
    assert result.parsed is not None
    assert isinstance(result.parsed, dict)
    assert "outline" in result.parsed