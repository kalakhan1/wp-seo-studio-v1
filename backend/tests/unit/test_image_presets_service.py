"""Unit tests for ImagePresetsService."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config.settings import Settings
from app.core.http_client import SafeHttpClient
from app.db.base import Base
from app.db.session import dispose_engine, init_engine
from app.models.connection import Connection
from app.security import secrets as secret_store
from app.services.image_presets_service import ImagePresetsService


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
        db_url=f"sqlite+aiosqlite:///{tmp_path / 'presets.db'}",
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
        label="preset-store",
        base_url="https://example.test",
        username="admin",
        auth_method="application_password",
        secret_ref="preset-store",
        require_https=True,
    )
    session.add(c)
    await session.commit()
    await session.refresh(c)
    secret_store.set_password(
        "wp-seo-studio", "conn:preset-store:wp_app_password", "abcd efgh"
    )
    return c


def _handler(routes: dict[tuple[str, str], tuple[int, Any]]) -> Any:
    def h(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        match = routes.get(key)
        if match is None:
            return httpx.Response(404, json={"code": "not_found"})
        status_code, body = match
        return httpx.Response(status_code, json=body)
    return h


MEDIA_JSON: dict[str, Any] = {
    "id": 101,
    "title": {"rendered": "test.jpg"},
    "source_url": "https://example.test/test.jpg",
    "mime_type": "image/jpeg",
    "media_details": {
        "width": 1200,
        "height": 1200,
        "sizes": {
            "thumbnail": {"width": 150, "height": 150, "crop": True},
            "medium": {"width": 300, "height": 300, "crop": False},
            "woocommerce_thumbnail": {"width": 300, "height": 300, "crop": True},
            "large": {"width": 1024, "height": 1024, "crop": False},
        },
    },
}


async def test_list_presets_returns_curated_lists(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    service = ImagePresetsService(
        settings=settings_for_service, session=db_session
    )
    result = await service.list_presets()
    assert len(result.suggested) >= 4
    assert len(result.css) >= 3


async def test_discover_uses_most_recent_media_when_no_id(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("GET", "/wp-json/wp/v2/media"): (200, [MEDIA_JSON]),
        ("GET", "/wp-json/wp/v2/media/101"): (200, MEDIA_JSON),
    }
    transport = httpx.MockTransport(_handler(routes))  # type: ignore[arg-type]
    service = ImagePresetsService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.discover_registered_sizes(
            connection_id=conn.id, media_id=None, http=http
        )
    assert result.source_media_id == 101
    names = {s.name for s in result.sizes}
    assert "thumbnail" in names
    assert "woocommerce_thumbnail" in names
    assert "large" in names


async def test_discover_with_explicit_media_id(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("GET", "/wp-json/wp/v2/media/101"): (200, MEDIA_JSON),
    }
    transport = httpx.MockTransport(_handler(routes))  # type: ignore[arg-type]
    service = ImagePresetsService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.discover_registered_sizes(
            connection_id=conn.id, media_id=101, http=http
        )
    assert result.source_media_id == 101
    assert len(result.sizes) == 4


async def test_discover_no_media_returns_warning(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("GET", "/wp-json/wp/v2/media"): (200, []),
    }
    transport = httpx.MockTransport(_handler(routes))  # type: ignore[arg-type]
    service = ImagePresetsService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.discover_registered_sizes(
            connection_id=conn.id, media_id=None, http=http
        )
    assert result.source_media_id == 0
    assert result.sizes == []
    assert any("no media" in w.lower() for w in result.warnings)