"""Integration tests for ConnectionService.

Uses:
  - In-memory SQLite (fresh schema per test)
  - Monkeypatched keyring (no real OS credential store)
  - httpx.MockTransport (no real network)
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config.settings import Settings
from app.core.exceptions import ValidationError
from app.core.http_client import SafeHttpClient
from app.db.base import Base
from app.db.session import dispose_engine, init_engine
from app.schemas.connection import (
    ConnectionSaveRequest,
    ConnectionTestRequest,
)
from app.security import secrets as secret_store
from app.services.connection_service import ConnectionService
from tests.fixtures.wp_responses import CURRENT_USER_JSON, SITE_INFO_JSON


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

    def _delete(label: str, field: str) -> None:
        key = secret_store._key(label, field)  # noqa: SLF001
        mem.store.pop((secret_store._SERVICE_NAME, key), None)

    monkeypatch.setattr(secret_store, "delete_secret", _delete)
    return mem


def _settings(tmp_path) -> Settings:  # type: ignore[no-untyped-def]
    return Settings(
        app_env="development",
        app_mode="mock",
        log_level="warning",
        http_timeout=5,
        http_max_retries=0,
        db_url=f"sqlite+aiosqlite:///{tmp_path / 'conn-test.db'}",
    )


@pytest.fixture
async def db_session(tmp_path) -> AsyncIterator[AsyncSession]:  # type: ignore[no-untyped-def]
    """Fresh SQLite DB with all tables created. Yields one session."""
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


def _wp_handler(routes: dict[str, tuple[int, object]]) -> object:
    def handler(request: httpx.Request) -> httpx.Response:
        match = routes.get(request.url.path)
        if match is None:
            return httpx.Response(404, json={"code": "rest_no_route"})
        status, body = match
        return httpx.Response(status, json=body)

    return handler


# --- Save & list ------------------------------------------------------------


async def test_save_stores_secrets_in_keyring_and_metadata_in_db(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    service = ConnectionService(settings=settings_for_service, session=db_session)
    payload = ConnectionSaveRequest(
        label="prod",
        base_url="https://example.com",
        username="admin",
        wp_app_password="abcd efgh",
        wc_consumer_key="ck_123",
        wc_consumer_secret="cs_456",
    )
    response = await service.save(payload)

    assert response.id > 0
    assert response.label == "prod"
    assert response.base_url == "https://example.com"
    assert response.has_wc_credentials is True

    assert (
        secret_store.get_secret("prod", secret_store.FIELD_WP_APP_PASSWORD)
        == "abcd efgh"
    )
    assert (
        secret_store.get_secret("prod", secret_store.FIELD_WC_CONSUMER_KEY)
        == "ck_123"
    )


async def test_save_duplicate_label_raises(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    service = ConnectionService(settings=settings_for_service, session=db_session)
    payload = ConnectionSaveRequest(
        label="prod",
        base_url="https://example.com",
        username="admin",
        wp_app_password="abcd efgh",
    )
    await service.save(payload)
    with pytest.raises(ValidationError):
        await service.save(payload)


async def test_save_rejects_http_when_require_https(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    service = ConnectionService(settings=settings_for_service, session=db_session)
    with pytest.raises(ValidationError):
        await service.save(
            ConnectionSaveRequest(
                label="prod",
                base_url="http://example.com",
                username="admin",
                wp_app_password="abcd efgh",
                require_https=True,
            )
        )


async def test_list_all_returns_saved(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    service = ConnectionService(settings=settings_for_service, session=db_session)
    await service.save(
        ConnectionSaveRequest(
            label="prod",
            base_url="https://example.com",
            username="admin",
            wp_app_password="abcd efgh",
        )
    )
    await service.save(
        ConnectionSaveRequest(
            label="staging",
            base_url="https://staging.example.com",
            username="admin",
            wp_app_password="abcd efgh",
        )
    )
    listed = await service.list_all()
    labels = {c.label for c in listed}
    assert labels == {"prod", "staging"}


async def test_delete_removes_metadata_and_secrets(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    service = ConnectionService(settings=settings_for_service, session=db_session)
    saved = await service.save(
        ConnectionSaveRequest(
            label="prod",
            base_url="https://example.com",
            username="admin",
            wp_app_password="abcd efgh",
        )
    )
    await service.delete(saved.id)

    listed = await service.list_all()
    assert listed == []
    assert (
        secret_store.get_secret("prod", secret_store.FIELD_WP_APP_PASSWORD)
        is None
    )


# --- Test connection --------------------------------------------------------


async def test_test_credentials_success(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    routes = {
        "/wp-json": (200, SITE_INFO_JSON),
        "/wp-json/wp/v2/users/me": (200, CURRENT_USER_JSON),
    }
    transport = httpx.MockTransport(_wp_handler(routes))  # type: ignore[arg-type]
    service = ConnectionService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.test_credentials(
            ConnectionTestRequest(
                base_url="https://example.com",
                username="admin",
                wp_app_password="abcd efgh",
                require_https=True,
            ),
            http=http,
        )
    assert result.ok is True
    assert result.site_info is not None
    assert result.site_info.name == "Herbal Care Demo"
    assert result.current_user is not None
    assert result.current_user.id == 7


async def test_test_credentials_auth_failure(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    routes = {
        "/wp-json": (200, SITE_INFO_JSON),
        "/wp-json/wp/v2/users/me": (401, {"code": "rest_cannot_access"}),
    }
    transport = httpx.MockTransport(_wp_handler(routes))  # type: ignore[arg-type]
    service = ConnectionService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.test_credentials(
            ConnectionTestRequest(
                base_url="https://example.com",
                username="admin",
                wp_app_password="wrong",
                require_https=True,
            ),
            http=http,
        )
    assert result.ok is False
    assert "Authentication failed" in result.message