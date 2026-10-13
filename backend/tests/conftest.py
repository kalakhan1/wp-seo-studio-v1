"""Shared pytest fixtures for the backend test suite.

Provides:
  - test_settings: isolated Settings pointed at a temp SQLite file
  - test_app: FastAPI app with dependency overrides and DB tables created
  - client: httpx.AsyncClient bound to test_app via ASGITransport
  - mock_wp_client: in-memory MockWordPressClient
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_settings_dep
from app.config.settings import Settings, get_settings
from app.db.base import Base
from app.db.session import dispose_engine, get_engine, init_engine
from app.main import create_app
from tests.mocks.mock_wordpress.client import MockWordPressClient


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Iterator[None]:
    """Ensure the cached Settings does not leak between tests.

    Sync fixture (uses plain yield), so the return type is Iterator[None],
    not AsyncIterator[None].
    """
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """Isolated Settings pointing to a temp SQLite file.

    Uses field names (populate_by_name=True) for readability.
    """
    db_path = tmp_path / "test.db"
    return Settings(
        app_env="development",
        app_debug=True,
        app_mode="mock",
        log_level="warning",
        log_format="human",
        db_url=f"sqlite+aiosqlite:///{db_path}",
    )


@pytest.fixture
async def test_app(test_settings: Settings) -> AsyncIterator[object]:
    """Create the FastAPI app with overridden settings and DB tables."""
    await dispose_engine()

    application = create_app(test_settings)
    application.dependency_overrides[get_settings_dep] = lambda: test_settings

    engine = init_engine(test_settings)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield application

    application.dependency_overrides.clear()
    await dispose_engine()


@pytest.fixture
async def client(test_app) -> AsyncIterator[AsyncClient]:  # type: ignore[no-untyped-def]
    """httpx.AsyncClient bound to test_app via ASGITransport."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_wp_client() -> MockWordPressClient:
    """Fresh in-memory mock WordPress client."""
    return MockWordPressClient()


@pytest.fixture
def ensure_engine_for_settings(test_settings: Settings):  # type: ignore[no-untyped-def]
    """Expose the initialized engine for integration tests that need raw access."""
    init_engine(test_settings)
    return get_engine()