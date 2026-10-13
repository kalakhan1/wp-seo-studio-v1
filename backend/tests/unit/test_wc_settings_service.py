"""Unit tests for WCSettingsService."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config.settings import Settings
from app.core.exceptions import ValidationError
from app.core.http_client import SafeHttpClient
from app.db.base import Base
from app.db.session import dispose_engine, init_engine
from app.models.connection import Connection
from app.schemas.wc_settings import WCSettingUpdateRequest
from app.security import secrets as secret_store
from app.services.wc_settings_service import WCSettingsService
from tests.fixtures.wc_responses import (
    WC_SETTINGS_CHECKOUT_JSON,
    WC_SETTINGS_GENERAL_JSON,
    WC_SETTINGS_PRODUCTS_JSON,
    WC_SETTINGS_TAX_JSON,
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
        db_url=f"sqlite+aiosqlite:///{tmp_path / 'wc-settings.db'}",
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
        label="wc-settings-store",
        base_url="https://example.test",
        username="admin",
        auth_method="application_password",
        secret_ref="wc-settings-store",
        require_https=True,
    )
    session.add(c)
    await session.commit()
    await session.refresh(c)
    secret_store.set_password(
        "wp-seo-studio",
        "conn:wc-settings-store:wp_app_password",
        "abcd efgh",
    )
    secret_store.set_password(
        "wp-seo-studio",
        "conn:wc-settings-store:wc_consumer_key",
        "ck_abc",
    )
    secret_store.set_password(
        "wp-seo-studio",
        "conn:wc-settings-store:wc_consumer_secret",
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


# --- Group reads ------------------------------------------------------------


async def test_list_groups_returns_known_groups(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    service = WCSettingsService(
        settings=settings_for_service, session=db_session
    )
    groups = await service.list_groups()
    assert "general" in groups
    assert "products" in groups
    assert "checkout" in groups


async def test_get_group_returns_settings(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("GET", "/wp-json/wc/v3/settings/general"): (200, WC_SETTINGS_GENERAL_JSON),
    }
    transport = httpx.MockTransport(_handler(routes))  # type: ignore[arg-type]
    service = WCSettingsService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.get_group(
            connection_id=conn.id, group="general", http=http
        )
    assert result.group == "general"
    assert any(s.id == "woocommerce_store_city" for s in result.settings)
    city = next(s for s in result.settings if s.id == "woocommerce_store_city")
    assert city.value == "Karachi"


async def test_get_group_rejects_unknown_group(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    service = WCSettingsService(
        settings=settings_for_service, session=db_session
    )
    with pytest.raises(ValidationError):
        async with SafeHttpClient(settings_for_service) as http:
            await service.get_group(
                connection_id=conn.id, group="does-not-exist", http=http
            )


# --- Update -----------------------------------------------------------------


async def test_update_setting_checkbox_accepts_bool(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("GET", "/wp-json/wc/v3/settings/checkout/woocommerce_enable_coupons"): (
            200,
            {
                "id": "woocommerce_enable_coupons",
                "type": "checkbox",
                "value": "yes",
                "label": "Enable coupons",
            },
        ),
        ("PUT", "/wp-json/wc/v3/settings/checkout/woocommerce_enable_coupons"): (
            200,
            {
                "id": "woocommerce_enable_coupons",
                "type": "checkbox",
                "value": "no",
                "label": "Enable coupons",
            },
        ),
    }
    transport = httpx.MockTransport(_handler(routes))  # type: ignore[arg-type]
    service = WCSettingsService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.update_setting(
            connection_id=conn.id,
            group="checkout",
            setting_id="woocommerce_enable_coupons",
            value=False,
            http=http,
        )
    assert result.value == "no"


async def test_update_setting_checkbox_rejects_invalid(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("GET", "/wp-json/wc/v3/settings/checkout/woocommerce_enable_coupons"): (
            200,
            {"id": "woocommerce_enable_coupons", "type": "checkbox", "value": "yes"},
        ),
    }
    transport = httpx.MockTransport(_handler(routes))  # type: ignore[arg-type]
    service = WCSettingsService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        with pytest.raises(ValidationError):
            await service.update_setting(
                connection_id=conn.id,
                group="checkout",
                setting_id="woocommerce_enable_coupons",
                value="maybe",
                http=http,
            )


async def test_update_setting_multiselect_accepts_list(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("GET", "/wp-json/wc/v3/settings/general/woocommerce_specific_allowed_countries"): (
            200,
            {
                "id": "woocommerce_specific_allowed_countries",
                "type": "multiselect",
                "value": [],
            },
        ),
        ("PUT", "/wp-json/wc/v3/settings/general/woocommerce_specific_allowed_countries"): (
            200,
            {
                "id": "woocommerce_specific_allowed_countries",
                "type": "multiselect",
                "value": ["PK", "US"],
            },
        ),
    }
    transport = httpx.MockTransport(_handler(routes))  # type: ignore[arg-type]
    service = WCSettingsService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.update_setting(
            connection_id=conn.id,
            group="general",
            setting_id="woocommerce_specific_allowed_countries",
            value=["PK", "US"],
            http=http,
        )
    assert result.value == ["PK", "US"]


# --- Store profile ----------------------------------------------------------


async def test_get_store_profile_complete(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    routes = {
        ("GET", "/wp-json/wc/v3/settings/general"): (200, WC_SETTINGS_GENERAL_JSON),
        ("GET", "/wp-json/wc/v3/settings/products"): (200, WC_SETTINGS_PRODUCTS_JSON),
        ("GET", "/wp-json/wc/v3/settings/tax"): (200, WC_SETTINGS_TAX_JSON),
        ("GET", "/wp-json/wc/v3/settings/checkout"): (200, WC_SETTINGS_CHECKOUT_JSON),
    }
    transport = httpx.MockTransport(_handler(routes))  # type: ignore[arg-type]
    service = WCSettingsService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.get_store_profile(
            connection_id=conn.id, http=http
        )
    assert result.profile.address.city == "Karachi"
    assert result.profile.address.country == "PK"
    assert result.profile.address.state == "SD"
    assert result.profile.currency == "PKR"
    assert result.profile.weight_unit == "kg"
    assert result.profile.guest_checkout_enabled is True
    assert result.profile.coupons_enabled is True
    # Checklist should be complete for required items
    required = [i for i in result.checklist.items if i.status == "missing"]
    assert len(required) == 0


async def test_get_store_profile_missing_items(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    empty_general: list[dict[str, Any]] = [
        {"id": "woocommerce_store_address", "type": "text", "value": ""},
        {"id": "woocommerce_store_city", "type": "text", "value": ""},
        {"id": "woocommerce_default_country", "type": "select", "value": ""},
        {"id": "woocommerce_currency", "type": "select", "value": ""},
    ]
    routes = {
        ("GET", "/wp-json/wc/v3/settings/general"): (200, empty_general),
        ("GET", "/wp-json/wc/v3/settings/products"): (200, []),
        ("GET", "/wp-json/wc/v3/settings/tax"): (200, []),
        ("GET", "/wp-json/wc/v3/settings/checkout"): (200, []),
    }
    transport = httpx.MockTransport(_handler(routes))  # type: ignore[arg-type]
    service = WCSettingsService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.get_store_profile(
            connection_id=conn.id, http=http
        )
    assert result.checklist.missing >= 3
    keys = {i.key for i in result.checklist.items if i.status == "missing"}
    assert "store_address" in keys
    assert "currency" in keys


async def test_get_store_profile_warns_on_country_without_state(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    general_no_state: list[dict[str, Any]] = [
        {"id": "woocommerce_store_address", "type": "text", "value": "X"},
        {"id": "woocommerce_store_city", "type": "text", "value": "Y"},
        {"id": "woocommerce_default_country", "type": "select", "value": "US"},
        {"id": "woocommerce_currency", "type": "select", "value": "USD"},
    ]
    routes = {
        ("GET", "/wp-json/wc/v3/settings/general"): (200, general_no_state),
        ("GET", "/wp-json/wc/v3/settings/products"): (200, []),
        ("GET", "/wp-json/wc/v3/settings/tax"): (200, []),
        ("GET", "/wp-json/wc/v3/settings/checkout"): (200, []),
    }
    transport = httpx.MockTransport(_handler(routes))  # type: ignore[arg-type]
    service = WCSettingsService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.get_store_profile(
            connection_id=conn.id, http=http
        )
    assert any("US" in w for w in result.warnings)


async def test_get_store_profile_warns_on_tax_mismatch(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection(db_session)
    tax_mismatch: list[dict[str, Any]] = [
        {"id": "woocommerce_calc_taxes", "type": "checkbox", "value": "no"},
        {"id": "woocommerce_prices_include_tax", "type": "checkbox", "value": "yes"},
    ]
    routes = {
        ("GET", "/wp-json/wc/v3/settings/general"): (200, []),
        ("GET", "/wp-json/wc/v3/settings/products"): (200, []),
        ("GET", "/wp-json/wc/v3/settings/tax"): (200, tax_mismatch),
        ("GET", "/wp-json/wc/v3/settings/checkout"): (200, []),
    }
    transport = httpx.MockTransport(_handler(routes))  # type: ignore[arg-type]
    service = WCSettingsService(
        settings=settings_for_service, session=db_session
    )
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.get_store_profile(
            connection_id=conn.id, http=http
        )
    assert any("tax" in w.lower() for w in result.warnings)


# --- Pydantic schema sanity -------------------------------------------------


def test_setting_update_request_accepts_any_json_value() -> None:
    assert WCSettingUpdateRequest(value=True).value is True
    assert WCSettingUpdateRequest(value="yes").value == "yes"
    assert WCSettingUpdateRequest(value=["PK", "US"]).value == ["PK", "US"]
    assert WCSettingUpdateRequest(value=42).value == 42