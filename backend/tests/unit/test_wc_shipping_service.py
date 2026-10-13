"""Unit tests for WCShippingService."""

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
from app.schemas.wc_shipping import (
    MethodAddRequest,
    MethodUpdateRequest,
    ZoneCreateRequest,
    ZoneLocation,
    ZoneUpdateRequest,
)
from app.security import secrets as secret_store
from app.services.wc_shipping_service import WCShippingService
from tests.fixtures.wc_responses import (
    WC_AVAILABLE_METHODS_JSON,
    WC_SHIPPING_ZONE_JSON,
    WC_SHIPPING_ZONES_LIST_JSON,
    WC_ZONE_LOCATIONS_JSON,
    WC_ZONE_METHODS_JSON,
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
        db_url=f"sqlite+aiosqlite:///{tmp_path / 'shipping.db'}",
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
        label="ship-store",
        base_url="https://example.test",
        username="admin",
        auth_method="application_password",
        secret_ref="ship-store",
        require_https=True,
    )
    session.add(c)
    await session.commit()
    await session.refresh(c)
    secret_store.set_password(
        "wp-seo-studio", "conn:ship-store:wp_app_password", "abcd efgh"
    )
    secret_store.set_password(
        "wp-seo-studio", "conn:ship-store:wc_consumer_key", "ck_abc"
    )
    secret_store.set_password(
        "wp-seo-studio", "conn:ship-store:wc_consumer_secret", "cs_xyz"
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


# --- List / get -------------------------------------------------------------


async def test_list_zones(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("GET", "/wp-json/wc/v3/shipping/zones"): (200, WC_SHIPPING_ZONES_LIST_JSON),
    }
    transport = httpx.MockTransport(_handler(routes))  # type: ignore[arg-type]
    service = WCShippingService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.list_zones(connection_id=conn.id, http=http)
    assert len(result.items) == 2
    assert result.items[0].name == "Pakistan"


async def test_get_zone_detail(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("GET", "/wp-json/wc/v3/shipping/zones/1"): (200, WC_SHIPPING_ZONE_JSON),
        ("GET", "/wp-json/wc/v3/shipping/zones/1/locations"): (
            200,
            WC_ZONE_LOCATIONS_JSON,
        ),
        ("GET", "/wp-json/wc/v3/shipping/zones/1/methods"): (
            200,
            WC_ZONE_METHODS_JSON,
        ),
    }
    transport = httpx.MockTransport(_handler(routes))  # type: ignore[arg-type]
    service = WCShippingService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        detail = await service.get_zone_detail(
            connection_id=conn.id, zone_id=1, http=http
        )
    assert detail.zone.id == 1
    assert len(detail.locations) == 1
    assert detail.locations[0].code == "PK"
    assert len(detail.methods) == 2
    assert detail.methods[0].method_id == "flat_rate"
    assert detail.methods[0].enabled is True


# --- Create -----------------------------------------------------------------


async def test_create_zone_with_locations(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    captured_locations: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        p = request.url.path
        m = request.method
        if m == "POST" and p == "/wp-json/wc/v3/shipping/zones":
            return httpx.Response(201, json=WC_SHIPPING_ZONE_JSON)
        if m == "PUT" and p == "/wp-json/wc/v3/shipping/zones/1/locations":
            import json as _json
            captured_locations["body"] = _json.loads(request.content.decode("utf-8"))
            return httpx.Response(200, json=WC_ZONE_LOCATIONS_JSON)
        if m == "GET" and p == "/wp-json/wc/v3/shipping/zones/1":
            return httpx.Response(200, json=WC_SHIPPING_ZONE_JSON)
        if m == "GET" and p == "/wp-json/wc/v3/shipping/zones/1/locations":
            return httpx.Response(200, json=WC_ZONE_LOCATIONS_JSON)
        if m == "GET" and p == "/wp-json/wc/v3/shipping/zones/1/methods":
            return httpx.Response(200, json=WC_ZONE_METHODS_JSON)
        return httpx.Response(404, json={"code": "not_found"})

    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]
    service = WCShippingService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        detail = await service.create_zone(
            connection_id=conn.id,
            payload=ZoneCreateRequest(
                name="Pakistan",
                locations=[ZoneLocation(code="PK", type="country")],
            ),
            http=http,
        )

    assert detail.zone.id == 1
    assert captured_locations["body"] == [{"code": "PK", "type": "country"}]


# --- Update / delete --------------------------------------------------------


async def test_update_zone_name(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        p = request.url.path
        m = request.method
        if m == "PUT" and p == "/wp-json/wc/v3/shipping/zones/1":
            import json as _json
            captured["body"] = _json.loads(request.content.decode("utf-8"))
            return httpx.Response(200, json=WC_SHIPPING_ZONE_JSON)
        if m == "GET" and p == "/wp-json/wc/v3/shipping/zones/1":
            return httpx.Response(200, json=WC_SHIPPING_ZONE_JSON)
        if m == "GET" and p == "/wp-json/wc/v3/shipping/zones/1/locations":
            return httpx.Response(200, json=[])
        if m == "GET" and p == "/wp-json/wc/v3/shipping/zones/1/methods":
            return httpx.Response(200, json=[])
        return httpx.Response(404, json={"code": "not_found"})

    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]
    service = WCShippingService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        await service.update_zone(
            connection_id=conn.id,
            zone_id=1,
            payload=ZoneUpdateRequest(name="Pakistan (updated)"),
            http=http,
        )
    assert captured["body"] == {"name": "Pakistan (updated)"}


async def test_delete_zone(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    called = {"delete": False}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "DELETE":
            called["delete"] = True
            return httpx.Response(200, json={"deleted": True})
        return httpx.Response(404, json={"code": "not_found"})

    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]
    service = WCShippingService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        await service.delete_zone(connection_id=conn.id, zone_id=1, http=http)
    assert called["delete"] is True


# --- Methods ----------------------------------------------------------------


async def test_add_method_wraps_settings(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            import json as _json
            captured["body"] = _json.loads(request.content.decode("utf-8"))
            return httpx.Response(201, json=WC_ZONE_METHODS_JSON[0])
        return httpx.Response(404, json={"code": "not_found"})

    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]
    service = WCShippingService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        method = await service.add_method(
            connection_id=conn.id,
            zone_id=1,
            payload=MethodAddRequest(
                method_id="flat_rate",
                title="Flat rate",
                enabled=True,
                settings={"cost": "150"},
            ),
            http=http,
        )
    assert method.method_id == "flat_rate"
    body = captured["body"]
    assert body["method_id"] == "flat_rate"
    assert body["settings"] == {"cost": {"value": "150"}}


async def test_update_method_requires_at_least_one_field(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    service = WCShippingService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service) as http:
        from app.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            await service.update_method(
                connection_id=conn.id,
                zone_id=1,
                instance_id=10,
                payload=MethodUpdateRequest(),
                http=http,
            )


async def test_delete_method(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    called = {"delete": False}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "DELETE":
            called["delete"] = True
            return httpx.Response(200, json={"deleted": True})
        return httpx.Response(404, json={"code": "not_found"})

    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]
    service = WCShippingService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        await service.delete_method(
            connection_id=conn.id, zone_id=1, instance_id=10, http=http
        )
    assert called["delete"] is True


async def test_list_available_methods(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("GET", "/wp-json/wc/v3/shipping_methods"): (200, WC_AVAILABLE_METHODS_JSON),
    }
    transport = httpx.MockTransport(_handler(routes))  # type: ignore[arg-type]
    service = WCShippingService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.list_available_methods(
            connection_id=conn.id, http=http
        )
    assert len(result.items) == 3
    ids = {m.id for m in result.items}
    assert {"flat_rate", "free_shipping", "local_pickup"}.issubset(ids)