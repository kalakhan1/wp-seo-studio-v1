"""Unit tests for SEOAuditService."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config.settings import Settings
from app.core.http_client import SafeHttpClient
from app.db.base import Base
from app.db.session import dispose_engine, init_engine
from app.models.connection import Connection
from app.models.media_record import MediaRecord
from app.security import secrets as secret_store
from app.services.seo_audit_service import SEOAuditService
from tests.fixtures.wp_responses import (
    CATEGORIES_JSON,
    NOT_FOUND_JSON,
    POST_JSON,
    SITE_INFO_JSON,
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
        db_url=f"sqlite+aiosqlite:///{tmp_path / 'audit.db'}",
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


async def _create_connection(
    session: AsyncSession,
    base_url: str = "https://example.test",
) -> Connection:
    c = Connection(
        label="audit-store",
        base_url=base_url,
        username="admin",
        auth_method="application_password",
        secret_ref="audit-store",
        require_https=True,
    )
    session.add(c)
    await session.commit()
    await session.refresh(c)
    secret_store.set_password(
        "wp-seo-studio", "conn:audit-store:wp_app_password", "abcd efgh"
    )
    return c


def _routes(
    routes: dict[tuple[str, str], tuple[int, object]]
):
    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        m = routes.get(key)
        if m is None:
            return httpx.Response(404, json=NOT_FOUND_JSON)
        code, body = m
        if isinstance(body, bytes):
            return httpx.Response(code, content=body)
        return httpx.Response(code, json=body)
    return handler


async def test_audit_https_pass(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session, "https://example.test")
    routes = {
        ("GET", "/wp-json"): (200, SITE_INFO_JSON),
        ("GET", "/wp-json/wp/v2/posts"): (200, [POST_JSON]),
        ("GET", "/wp-json/wp/v2/categories"): (200, CATEGORIES_JSON),
        ("GET", "/sitemap_index.xml"): (200, b"<urlset></urlset>"),
        ("GET", "/robots.txt"): (200, b"Sitemap: https://example.test/sitemap_index.xml\n"),
    }
    transport = httpx.MockTransport(_routes(routes))  # type: ignore[arg-type]
    service = SEOAuditService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        report = await service.run(connection_id=conn.id, http=http)

    https = next(f for f in report.findings if f.check_id == "https.enabled")
    assert https.severity == "pass"
    sitemap = next(f for f in report.findings if f.check_id == "sitemap.reachable")
    assert sitemap.severity == "pass"
    robots = next(f for f in report.findings if f.check_id == "robots.reachable")
    assert robots.severity == "pass"
    assert report.run_id is not None


async def test_audit_https_fail(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session, "http://example.test")
    routes = {
        ("GET", "/wp-json"): (200, SITE_INFO_JSON),
        ("GET", "/wp-json/wp/v2/posts"): (200, [POST_JSON]),
        ("GET", "/wp-json/wp/v2/categories"): (200, []),
        ("GET", "/sitemap_index.xml"): (404, {}),
        ("GET", "/wp-sitemap.xml"): (404, {}),
        ("GET", "/sitemap.xml"): (404, {}),
        ("GET", "/robots.txt"): (200, b"Disallow: /\n"),
    }
    transport = httpx.MockTransport(_routes(routes))  # type: ignore[arg-type]
    service = SEOAuditService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        report = await service.run(connection_id=conn.id, http=http)

    https = next(f for f in report.findings if f.check_id == "https.enabled")
    assert https.severity == "fail"
    robots = next(f for f in report.findings if f.check_id == "robots.reachable")
    assert robots.severity == "fail"
    assert report.summary.fail_count >= 2


async def test_audit_media_alt_text_warns(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    db_session.add_all(
        [
            MediaRecord(
                connection_id=conn.id,
                filename="a.jpg",
                alt_text="",
            ),
            MediaRecord(
                connection_id=conn.id,
                filename="b.jpg",
                alt_text="A nice image",
            ),
        ]
    )
    await db_session.commit()

    routes = {
        ("GET", "/wp-json"): (200, SITE_INFO_JSON),
        ("GET", "/wp-json/wp/v2/posts"): (200, [POST_JSON]),
        ("GET", "/wp-json/wp/v2/categories"): (200, []),
        ("GET", "/sitemap_index.xml"): (200, b"<x></x>"),
        ("GET", "/robots.txt"): (200, b"Sitemap: x\n"),
    }
    transport = httpx.MockTransport(_routes(routes))  # type: ignore[arg-type]
    service = SEOAuditService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        report = await service.run(connection_id=conn.id, http=http)

    media = next(f for f in report.findings if f.check_id == "media.alt_text")
    assert media.severity == "warn"
    assert media.evidence.get("missing") == 1
    assert media.evidence.get("total") == 2


async def test_audit_history_persists(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("GET", "/wp-json"): (200, SITE_INFO_JSON),
        ("GET", "/wp-json/wp/v2/posts"): (200, [POST_JSON]),
        ("GET", "/wp-json/wp/v2/categories"): (200, CATEGORIES_JSON),
        ("GET", "/sitemap_index.xml"): (200, b"<x></x>"),
        ("GET", "/robots.txt"): (200, b"Sitemap: x\n"),
    }
    transport = httpx.MockTransport(_routes(routes))  # type: ignore[arg-type]
    service = SEOAuditService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        await service.run(connection_id=conn.id, http=http)

    history = await service.history(connection_id=conn.id)
    assert len(history.items) == 1
    assert history.items[0].site_url == "https://example.test"