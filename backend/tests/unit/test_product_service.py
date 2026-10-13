"""Unit tests for ProductService orchestration."""

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
from app.models.connection import Connection
from app.models.publish_history import PublishHistory
from app.schemas.product import (
    ProductCreateRequest,
    ProductUpdateRequest,
)
from app.security import secrets as secret_store
from app.services.product_service import ProductService
from tests.fixtures.wc_responses import WC_PRODUCT_JSON


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
        db_url=f"sqlite+aiosqlite:///{tmp_path / 'prod.db'}",
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


async def _create_connection_with_wc(session: AsyncSession) -> Connection:
    c = Connection(
        label="wc-store",
        base_url="https://example.test",
        username="admin",
        auth_method="application_password",
        secret_ref="wc-store",
        require_https=True,
    )
    session.add(c)
    await session.commit()
    await session.refresh(c)
    secret_store.set_password(
        "wp-seo-studio",
        "conn:wc-store:wp_app_password",
        "abcd efgh",
    )
    secret_store.set_password(
        "wp-seo-studio",
        "conn:wc-store:wc_consumer_key",
        "ck_abc",
    )
    secret_store.set_password(
        "wp-seo-studio",
        "conn:wc-store:wc_consumer_secret",
        "cs_xyz",
    )
    return c


def _wp_handler(routes: dict[tuple[str, str], tuple[int, Any]]) -> Any:
    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        match = routes.get(key)
        if match is None:
            return httpx.Response(404, json={"code": "not_found"})
        status_code, body = match
        return httpx.Response(status_code, json=body)
    return handler


# --- Create -----------------------------------------------------------------


async def test_create_product_success_no_rank_math(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection_with_wc(db_session)
    routes = {
        ("POST", "/wp-json/wc/v3/products"): (201, WC_PRODUCT_JSON),
    }
    transport = httpx.MockTransport(_wp_handler(routes))  # type: ignore[arg-type]
    service = ProductService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.create(
            ProductCreateRequest(
                connection_id=conn.id,
                name="Herbal Hair Oil",
                status="draft",
                regular_price="499.00",
                sku="HHO-001",
                category_ids=[5],
                tag_ids=[10],
            ),
            http=http,
        )

    assert result.success is True
    assert result.partial is False
    assert result.wp_object_id == 501
    assert result.sku == "HHO-001"


async def test_create_product_with_rank_math(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection_with_wc(db_session)
    routes = {
        ("POST", "/wp-json/wc/v3/products"): (201, WC_PRODUCT_JSON),
        ("POST", "/wp-json/wp-seo-control/v1/rankmath/meta/501"): (
            200,
            {"ok": True, "post_id": 501, "meta": {"title": "SEO"}},
        ),
    }
    transport = httpx.MockTransport(_wp_handler(routes))  # type: ignore[arg-type]
    service = ProductService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.create(
            ProductCreateRequest(
                connection_id=conn.id,
                name="Herbal Hair Oil",
                rank_math=RankMathMeta(title="SEO", focus_keyword="oil"),
            ),
            http=http,
        )

    assert result.rank_math_written is True
    assert result.partial is False


async def test_create_product_partial_when_companion_missing(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection_with_wc(db_session)
    routes = {
        ("POST", "/wp-json/wc/v3/products"): (201, WC_PRODUCT_JSON),
    }
    transport = httpx.MockTransport(_wp_handler(routes))  # type: ignore[arg-type]
    service = ProductService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.create(
            ProductCreateRequest(
                connection_id=conn.id,
                name="Herbal Hair Oil",
                rank_math=RankMathMeta(title="SEO"),
            ),
            http=http,
        )

    assert result.success is True
    assert result.partial is True
    assert result.rank_math_written is False
    assert "Companion plugin" in (result.rank_math_error or "")


async def test_create_product_records_history(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection_with_wc(db_session)
    routes = {
        ("POST", "/wp-json/wc/v3/products"): (201, WC_PRODUCT_JSON),
    }
    transport = httpx.MockTransport(_wp_handler(routes))  # type: ignore[arg-type]
    service = ProductService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        await service.create(
            ProductCreateRequest(connection_id=conn.id, name="Herbal Hair Oil"),
            http=http,
        )

    result = await db_session.execute(select(PublishHistory))
    rows = result.scalars().all()
    assert len(rows) == 1
    assert rows[0].object_type == "product"
    assert rows[0].operation == "create"
    assert rows[0].status == "success"


# --- Update -----------------------------------------------------------------


async def test_update_product_success(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection_with_wc(db_session)
    routes = {
        ("PUT", "/wp-json/wc/v3/products/501"): (200, WC_PRODUCT_JSON),
    }
    transport = httpx.MockTransport(_wp_handler(routes))  # type: ignore[arg-type]
    service = ProductService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.update(
            product_id=501,
            payload=ProductUpdateRequest(
                connection_id=conn.id,
                regular_price="199.00",
            ),
            http=http,
        )

    assert result.success is True
    assert result.wp_object_id == 501


# --- Get --------------------------------------------------------------------


async def test_get_product_without_companion(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    conn = await _create_connection_with_wc(db_session)
    routes = {
        ("GET", "/wp-json/wc/v3/products/501"): (200, WC_PRODUCT_JSON),
    }
    transport = httpx.MockTransport(_wp_handler(routes))  # type: ignore[arg-type]
    service = ProductService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service, transport=transport) as http:
        result = await service.get(
            product_id=501,
            connection_id=conn.id,
            http=http,
        )

    assert result.id == 501
    assert result.sku == "HHO-001"
    assert result.category_ids == [5]
    assert result.rank_math_available is False


# --- Missing WC credentials -------------------------------------------------


async def test_create_product_without_wc_keys_raises(
    db_session: AsyncSession,
    settings_for_service: Settings,
    memory_keyring: _MemoryKeyring,
) -> None:
    c = Connection(
        label="no-wc",
        base_url="https://example.test",
        username="admin",
        auth_method="application_password",
        secret_ref="no-wc",
        require_https=True,
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    secret_store.set_password(
        "wp-seo-studio",
        "conn:no-wc:wp_app_password",
        "abcd efgh",
    )
    # No WC keys stored.

    from app.core.exceptions import ValidationError

    service = ProductService(settings=settings_for_service, session=db_session)
    async with SafeHttpClient(settings_for_service) as http:
        with pytest.raises(ValidationError):
            await service.create(
                ProductCreateRequest(connection_id=c.id, name="X"),
                http=http,
            )