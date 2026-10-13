"""FastAPI dependency providers.

Kept intentionally thin so routers stay testable and simple. Anything that
needs to be overridden in tests is exposed as a function here.
"""

from __future__ import annotations

from typing import Annotated, AsyncIterator

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings
from app.db.session import get_session


# --- Settings ---------------------------------------------------------------


def get_settings_dep() -> Settings:
    """Return the cached Settings instance."""
    return get_settings()


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]


# --- Database session -------------------------------------------------------


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield a DB session. Delegates to app.db.session.get_session."""
    async for session in get_session():
        yield session


DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


# --- Request id -------------------------------------------------------------


def get_request_id(
    request: Request,
    x_request_id: Annotated[str | None, Header(alias="X-Request-ID")] = None,
) -> str:
    """Return the request id.

    Precedence: X-Request-ID header -> value set by middleware -> empty string.
    Middleware (see app.main) sets request.state.request_id on every request.
    """
    if x_request_id:
        return x_request_id
    return getattr(request.state, "request_id", "") or ""


RequestIdDep = Annotated[str, Depends(get_request_id)]


# --- WordPress client placeholder -------------------------------------------


class _UnavailableWPClient:
    """Placeholder for Phase 2.

    The real client will be constructed from Settings + a stored Connection.
    Until then, any attempt to use it raises a clear error instead of
    silently doing nothing.
    """

    def __init__(self) -> None:
        self.available = False

    def __getattr__(self, name: str) -> object:
        raise RuntimeError(
            "WordPress client is not available in Phase 1. "
            "Complete Phase 2 (connection & capability discovery) first."
        )


def get_wp_client_placeholder() -> _UnavailableWPClient:
    """Phase 1 placeholder. Replaced in Phase 2 with a real dependency."""
    return _UnavailableWPClient()


WPClientPlaceholderDep = Annotated[_UnavailableWPClient, Depends(get_wp_client_placeholder)]