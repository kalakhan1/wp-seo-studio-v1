"""Unit tests for WCGatewayService."""

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
from app.schemas.wc_gateway import CODSettings
from app.security import secrets as secret_store
from app.services.wc_gateway_service import WCGatewayService
from tests.fixtures.wp_responses import WC_SHIPPING_ZONES_JSON
from tests.fixtures.wc_responses import (
    WC_GATEWAY_BACS_JSON,
    WC_GATEWAY_COD_DISABLED_JSON,
    WC_GATEWAY_COD_ENABLED_JSON,
    WC_GATEWAY_LIST_JSON,
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
        db_url=f"sqlite+aiosqlite:///{tmp_path / 'gw.db'}",
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
        label="gw-store",
        base_url="https://example.test",
        username="admin",
        auth_method="application_password",
        secret_ref="gw-store",
        require_https=True,
    )
    session.add(c)
    await session.commit()
    await session.refresh(c)
    secret_store.set_password(
        "wp-seo-studio",
        "conn:gw-store:wp_app_password",
        "abcd efgh",
    )
    secret_store.set_password(
        "wp-seo-studio",
        "conn:gw-store:wc_consumer_key",
        "ck_abc",
    )
    secret_store.set_password(
        "wp-seo-studio",
        "conn:gw-store:wc_consumer_secret",
        "cs_xyz",
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


# --- List -------------------------------------------------------------------


async def test_list_gateways(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("GET", "/wp-json/wc/v3/payment_gateways"): (200, WC_GATEWAY_LIST_JSON),
    }
    transport = httpx.MockTransport(_handler(routes))  # type: ignore[arg-type]
    service = WCGatewayService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.list_gateways(
            connection_id=conn.id, http=http
        )
    assert len(result.items) == 2
    cod = next(g for g in result.items if g.id == "cod")
    assert cod.enabled is True
    assert cod.title == "Cash on delivery"


# --- COD status -------------------------------------------------------------


async def test_cod_status_enabled_with_shipping_zones(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("GET", "/wp-json/wc/v3/payment_gateways/cod"): (
            200,
            WC_GATEWAY_COD_ENABLED_JSON,
        ),
        ("GET", "/wp-json/wc/v3/shipping/zones"): (200, WC_SHIPPING_ZONES_JSON),
    }
    transport = httpx.MockTransport(_handler(routes))  # type: ignore[arg-type]
    service = WCGatewayService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        status = await service.get_cod_status(
            connection_id=conn.id, http=http
        )
    assert status.available is True
    assert status.enabled is True
    assert status.shipping_zones_available is True
    assert status.instructions == "Please have exact change ready."
    assert status.warnings == []


async def test_cod_status_disabled(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("GET", "/wp-json/wc/v3/payment_gateways/cod"): (
            200,
            WC_GATEWAY_COD_DISABLED_JSON,
        ),
        ("GET", "/wp-json/wc/v3/shipping/zones"): (200, WC_SHIPPING_ZONES_JSON),
    }
    transport = httpx.MockTransport(_handler(routes))  # type: ignore[arg-type]
    service = WCGatewayService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        status = await service.get_cod_status(
            connection_id=conn.id, http=http
        )
    assert status.available is True
    assert status.enabled is False


async def test_cod_status_missing_gateway_warns(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes: dict[tuple[str, str], tuple[int, Any]] = {}
    transport = httpx.MockTransport(_handler(routes))  # type: ignore[arg-type]
    service = WCGatewayService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        status = await service.get_cod_status(
            connection_id=conn.id, http=http
        )
    assert status.available is False
    assert status.enabled is False
    assert any("not found" in w.lower() for w in status.warnings)


async def test_cod_status_warns_when_no_shipping_zones(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("GET", "/wp-json/wc/v3/payment_gateways/cod"): (
            200,
            WC_GATEWAY_COD_ENABLED_JSON,
        ),
        ("GET", "/wp-json/wc/v3/shipping/zones"): (200, []),
    }
    transport = httpx.MockTransport(_handler(routes))  # type: ignore[arg-type]
    service = WCGatewayService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        status = await service.get_cod_status(
            connection_id=conn.id, http=http
        )
    assert status.shipping_zones_available is False
    assert any("shipping zone" in w.lower() for w in status.warnings)


# --- COD update -------------------------------------------------------------


async def test_update_cod_enable(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)

    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if (
            request.method == "PUT"
            and request.url.path == "/wp-json/wc/v3/payment_gateways/cod"
        ):
            import json as _json

            captured["body"] = _json.loads(request.content.decode("utf-8"))
            return httpx.Response(200, json=WC_GATEWAY_COD_ENABLED_JSON)
        return httpx.Response(404, json={"code": "not_found"})

    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]
    service = WCGatewayService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.update_cod(
            connection_id=conn.id,
            payload=CODSettings(enabled=True, title="Pay cash"),
            http=http,
        )
    assert result.id == "cod"
    body = captured["body"]
    assert body["enabled"] is True
    assert body["title"] == "Pay cash"


async def test_update_cod_requires_at_least_one_field(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    service = WCGatewayService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service) as http:
        from app.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            await service.update_cod(
                connection_id=conn.id,
                payload=CODSettings(),
                http=http,
            )


async def test_update_cod_instructions_wrapped_correctly(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)

    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json as _json

        captured["body"] = _json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json=WC_GATEWAY_COD_ENABLED_JSON)

    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]
    service = WCGatewayService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        await service.update_cod(
            connection_id=conn.id,
            payload=CODSettings(
                instructions="Please have exact change ready.",
                enable_for_virtual=False,
            ),
            http=http,
        )

    body = captured["body"]
    assert "settings" in body
    assert body["settings"]["instructions"]["value"] == (
        "Please have exact change ready."
    )
    assert body["settings"]["enable_for_virtual"]["value"] == "no"