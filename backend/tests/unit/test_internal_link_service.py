"""Unit tests for InternalLinkService."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config.settings import Settings
from app.db.base import Base
from app.db.session import dispose_engine, init_engine
from app.models.connection import Connection
from app.security import secrets as secret_store
from app.services.internal_link_service import (
    InternalLinkService,
    _similarity,
    _tokenize,
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
        db_url=f"sqlite+aiosqlite:///{tmp_path / 'ilinks.db'}",
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
    session: AsyncSession, base_url: str = "https://example.test"
) -> Connection:
    c = Connection(
        label="ilink-store",
        base_url=base_url,
        username="admin",
        auth_method="application_password",
        secret_ref="ilink-store",
        require_https=True,
    )
    session.add(c)
    await session.commit()
    await session.refresh(c)
    secret_store.set_password(
        "wp-seo-studio", "conn:ilink-store:wp_app_password", "abcd efgh"
    )
    secret_store.set_password(
        "wp-seo-studio", "conn:ilink-store:wc_consumer_key", "ck_abc"
    )
    secret_store.set_password(
        "wp-seo-studio", "conn:ilink-store:wc_consumer_secret", "cs_xyz"
    )
    return c


# --- Pure helpers ----------------------------------------------------------


def test_tokenize_lowercase_and_min_length() -> None:
    tokens = _tokenize("Herbal hair oil is oil")
    assert "herbal" in tokens
    assert "hair" in tokens
    assert "oil" in tokens
    assert "is" not in tokens  # too short


def test_similarity_identical_is_one() -> None:
    assert _similarity("herbal hair oil", "herbal hair oil") == 1.0


def test_similarity_disjoint_is_zero() -> None:
    assert _similarity("herbal hair oil", "laptop battery") == 0.0


def test_similarity_partial() -> None:
    score = _similarity("herbal hair oil", "herbal hair oil guide")
    assert 0.5 < score < 1.0


# --- URL validation --------------------------------------------------------


async def test_validate_url_accepts_matching_host(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session, "https://example.test")
    service = InternalLinkService(
        settings=settings_for_service, session=db_session
    )
    result = await service.validate_url(
        connection_id=conn.id,
        url="https://example.test/blog/post/",
    )
    assert result.ok is True
    assert result.host == "example.test"


async def test_validate_url_rejects_other_host(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session, "https://example.test")
    service = InternalLinkService(
        settings=settings_for_service, session=db_session
    )
    result = await service.validate_url(
        connection_id=conn.id,
        url="https://other.example.com/",
    )
    assert result.ok is False
    assert "does not match" in result.reason


async def test_validate_url_rejects_invalid_scheme(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    service = InternalLinkService(
        settings=settings_for_service, session=db_session
    )
    result = await service.validate_url(
        connection_id=conn.id,
        url="ftp://example.test/file",
    )
    assert result.ok is False


async def test_validate_url_rejects_empty_host(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    service = InternalLinkService(
        settings=settings_for_service, session=db_session
    )
    result = await service.validate_url(
        connection_id=conn.id,
        url="https:///no-host",
    )
    assert result.ok is False


# --- Anchor text -----------------------------------------------------------


async def test_anchor_text_warns_on_repeated_exact(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    service = InternalLinkService(
        settings=settings_for_service, session=db_session
    )
    result = await service.check_anchor_text(
        anchor_text="herbal oil",
        existing_anchors=["herbal oil", "herbal oil", "herbal oil"],
    )
    assert result.exact_match_count == 3
    assert len(result.warnings) >= 1


async def test_anchor_text_no_warning_for_single_use(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    service = InternalLinkService(
        settings=settings_for_service, session=db_session
    )
    result = await service.check_anchor_text(
        anchor_text="herbal oil",
        existing_anchors=["herbal oil", "something else"],
    )
    assert result.exact_match_count == 1
    assert result.warnings == []


async def test_anchor_text_rejects_empty(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    service = InternalLinkService(
        settings=settings_for_service, session=db_session
    )
    result = await service.check_anchor_text(
        anchor_text="   ",
        existing_anchors=[],
    )
    assert "empty" in result.warnings[0].lower()