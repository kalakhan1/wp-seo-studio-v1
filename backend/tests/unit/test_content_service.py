"""Unit tests for ContentService.

Uses in-memory SQLite + MockTransport. Tests the orchestration logic:
creation, update, Rank Math meta handling, and truthful partial-success
reporting.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config.settings import Settings
from app.core.http_client import SafeHttpClient
from app.db.base import Base
from app.db.session import dispose_engine, init_engine
from app.integrations.rankmath.types import RankMathMeta
from app.integrations.wordpress.exceptions import WPAuthError
from app.models.connection import Connection
from app.models.publish_history import PublishHistory
from app.schemas.content import (
    ContentCreateRequest,
    ContentUpdateRequest,
)
from app.security import secrets as secret_store
from app.services.content_service import ContentService
from tests.fixtures.wp_responses import (
    FORBIDDEN_JSON,
    NOT_FOUND_JSON,
    PAGE_JSON,
    POST_JSON,
)


class _MemoryKeyring:
    def __init__(self) -> None:
        self.store: dict[tuple[str, str], str] = {}


@pytest.fixture
def memory_keyring(monkeypatch: pytest.MonkeyPatch) -> _MemoryKeyring:
    mem = _MemoryKeyring()

    def _set(service: str, key: str, value: str) -> None:
        mem.store[(service, key)] = value

    def _get(service: str, key: str) -> str | None:
        return mem.store.get((service, key))

    monkeypatch.setattr(secret_store, "set_password", _set)
    monkeypatch.setattr(secret_store, "get_password", _get)
    return mem


def _settings(tmp_path) -> Settings:  # type: ignore[no-untyped-def]
    return Settings(
        app_env="development",
        app_mode="mock",
        log_level="warning",
        http_timeout=5,
        http_max_retries=0,
        http_max_response_bytes=5_000_000,
        db_url=f"sqlite+aiosqlite:///{tmp_path / 'content.db'}",
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


async def _create_connection(session: AsyncSession) -> Connection:
    c = Connection(
        label="prod",
        base_url="https://example.test",
        username="admin",
        auth_method="application_password",
        secret_ref="prod",
        require_https=True,
    )
    session.add(c)
    await session.commit()
    await session.refresh(c)
    # Store keyring secret
    secret_store.set_password(
        "wp-seo-studio",
        "conn:prod:wp_app_password",
        "abcd efgh",
    )
    return c


def _wp_handler(routes: dict[tuple[str, str], tuple[int, Any]]) -> Any:
    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        match = routes.get(key)
        if match is None:
            return httpx.Response(404, json=NOT_FOUND_JSON)
        status_code, body = match
        return httpx.Response(status_code, json=body)
    return handler


# --- Create -----------------------------------------------------------------


async def test_create_post_success_no_rank_math(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("POST", "/wp-json/wp/v2/posts"): (201, POST_JSON),
    }
    transport = httpx.MockTransport(_wp_handler(routes))  # type: ignore[arg-type]
    service = ContentService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.create(
            ContentCreateRequest(
                connection_id=conn.id,
                kind="post",
                title="Badam Benefits Guide",
                content="<p>Badam is a nutrient-dense nut.</p>",
                status="draft",
                slug="badam-benefits-guide",
            ),
            http=http,
        )

    assert result.success is True
    assert result.partial is False
    assert result.wp_object_id == 202
    assert result.wp_object_type == "post"
    assert result.rank_math_written is False
    assert result.rank_math_error is None


async def test_create_post_success_with_rank_math(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("POST", "/wp-json/wp/v2/posts"): (201, POST_JSON),
        ("POST", "/wp-json/wp-seo-control/v1/rankmath/meta/202"): (
            200,
            {
                "ok": True,
                "post_id": 202,
                "meta": {"title": "SEO Title", "focus_keyword": "badam"},
            },
        ),
    }
    transport = httpx.MockTransport(_wp_handler(routes))  # type: ignore[arg-type]
    service = ContentService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.create(
            ContentCreateRequest(
                connection_id=conn.id,
                kind="post",
                title="Badam Benefits Guide",
                status="draft",
                rank_math=RankMathMeta(
                    title="SEO Title",
                    description="SEO Description",
                    focus_keyword="badam",
                ),
            ),
            http=http,
        )

    assert result.success is True
    assert result.partial is False
    assert result.rank_math_written is True
    assert result.rank_math_error is None


async def test_create_post_partial_when_companion_missing(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("POST", "/wp-json/wp/v2/posts"): (201, POST_JSON),
        # No rank math meta route — companion plugin is missing.
    }
    transport = httpx.MockTransport(_wp_handler(routes))  # type: ignore[arg-type]
    service = ContentService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.create(
            ContentCreateRequest(
                connection_id=conn.id,
                kind="post",
                title="Badam Benefits Guide",
                status="draft",
                rank_math=RankMathMeta(title="SEO Title", focus_keyword="badam"),
            ),
            http=http,
        )

    assert result.success is True
    assert result.partial is True
    assert result.wp_object_id == 202
    assert result.rank_math_written is False
    assert result.rank_math_error is not None
    assert "Companion plugin" in result.rank_math_error


async def test_create_post_fails_when_wp_rejects(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("POST", "/wp-json/wp/v2/posts"): (403, FORBIDDEN_JSON),
    }
    transport = httpx.MockTransport(_wp_handler(routes))  # type: ignore[arg-type]
    service = ContentService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        with pytest.raises(WPAuthError):
            await service.create(
                ContentCreateRequest(
                    connection_id=conn.id,
                    kind="post",
                    title="Badam Benefits Guide",
                    status="draft",
                ),
                http=http,
            )

    # Failed operation should be recorded
    result = await db_session.execute(
        select(PublishHistory).where(PublishHistory.status == "failed")
    )
    failures = result.scalars().all()
    assert len(failures) == 1
    assert failures[0].object_type == "post"


async def test_create_page_success(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("POST", "/wp-json/wp/v2/pages"): (201, PAGE_JSON),
    }
    transport = httpx.MockTransport(_wp_handler(routes))  # type: ignore[arg-type]
    service = ContentService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.create(
            ContentCreateRequest(
                connection_id=conn.id,
                kind="page",
                title="About Us",
                content="<p>We sell herbal products.</p>",
                status="publish",
            ),
            http=http,
        )

    assert result.success is True
    assert result.wp_object_id == 303
    assert result.wp_object_type == "page"


# --- History ----------------------------------------------------------------


async def test_create_records_history(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("POST", "/wp-json/wp/v2/posts"): (201, POST_JSON),
    }
    transport = httpx.MockTransport(_wp_handler(routes))  # type: ignore[arg-type]
    service = ContentService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        await service.create(
            ContentCreateRequest(
                connection_id=conn.id,
                kind="post",
                title="Test",
                status="draft",
            ),
            http=http,
        )

    result = await db_session.execute(select(PublishHistory))
    rows = result.scalars().all()
    assert len(rows) == 1
    assert rows[0].operation == "create"
    assert rows[0].status == "success"
    assert rows[0].wp_object_id == 202


# --- Update -----------------------------------------------------------------


async def test_update_post_success(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("POST", "/wp-json/wp/v2/posts/202"): (200, POST_JSON),
    }
    transport = httpx.MockTransport(_wp_handler(routes))  # type: ignore[arg-type]
    service = ContentService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.update(
            kind="post",
            wp_object_id=202,
            payload=ContentUpdateRequest(
                connection_id=conn.id,
                title="Updated Title",
            ),
            http=http,
        )

    assert result.success is True
    assert result.wp_object_id == 202

    # History records update
    result_h = await db_session.execute(
        select(PublishHistory).where(PublishHistory.operation == "update")
    )
    rows = result_h.scalars().all()
    assert len(rows) == 1


# --- Get --------------------------------------------------------------------


async def test_get_post_without_companion(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("GET", "/wp-json/wp/v2/posts/202"): (200, POST_JSON),
    }
    transport = httpx.MockTransport(_wp_handler(routes))  # type: ignore[arg-type]
    service = ContentService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.get(
            kind="post",
            wp_object_id=202,
            connection_id=conn.id,
            http=http,
        )

    assert result.id == 202
    assert result.kind == "post"
    assert result.rank_math_available is False
    assert result.rank_math_reason is not None


async def test_get_post_with_companion(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("GET", "/wp-json/wp/v2/posts/202"): (200, POST_JSON),
        ("GET", "/wp-json/wp-seo-control/v1/rankmath/meta/202"): (
            200,
            {
                "ok": True,
                "post_id": 202,
                "meta": {
                    "title": "SEO Title",
                    "focus_keyword": "badam",
                },
            },
        ),
    }
    transport = httpx.MockTransport(_wp_handler(routes))  # type: ignore[arg-type]
    service = ContentService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.get(
            kind="post",
            wp_object_id=202,
            connection_id=conn.id,
            http=http,
        )

    assert result.rank_math_available is True
    assert result.rank_math is not None
    assert result.rank_math.title == "SEO Title"
    assert result.rank_math.focus_keyword == "badam"