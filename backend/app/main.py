"""FastAPI application factory.

Responsibilities:
  - Load settings and configure logging
  - Initialize DB engine
  - Register middleware (request id, CORS, error handler)
  - Mount API v1 router
  - Handle startup/shutdown cleanly
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __app_name__, __version__
from app.api.v1.router import api_v1_router
from app.config.constants import API_V1_PREFIX
from app.config.logging import configure_logging, get_logger
from app.config.settings import Settings, get_settings
from app.core.exceptions import AppError
from app.db.session import dispose_engine, init_engine

REQUEST_ID_HEADER = "X-Request-ID"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown hooks."""
    settings: Settings = app.state.settings
    log = get_logger(__name__)

    # Startup
    init_engine(settings)
    log.info(
        "app_startup",
        version=__version__,
        env=settings.app_env.value,
        mode=settings.effective_app_mode.value,
        host=settings.app_host,
        port=settings.app_port,
    )

    try:
        yield
    finally:
        # Shutdown
        await dispose_engine()
        log.info("app_shutdown")


def _register_middlewares(app: FastAPI, settings: Settings) -> None:
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=[REQUEST_ID_HEADER],
    )

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        """Attach a request id, log request start/finish, add response header."""
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming or uuid.uuid4().hex
        request.state.request_id = request_id

        log = get_logger("http")
        log.info(
            "request_start",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        try:
            response = await call_next(request)
        except Exception as exc:  # noqa: BLE001 - we want to log then re-raise
            log.error(
                "request_unhandled_exception",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=exc.__class__.__name__,
            )
            raise

        response.headers[REQUEST_ID_HEADER] = request_id
        log.info(
            "request_end",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
        )
        return response


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "")
        return JSONResponse(
            status_code=exc.http_status,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
                "request_id": request_id,
            },
            headers={REQUEST_ID_HEADER: request_id} if request_id else None,
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "")
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed.",
                    "details": {"errors": exc.errors()},
                },
                "request_id": request_id,
            },
            headers={REQUEST_ID_HEADER: request_id} if request_id else None,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": str(exc.detail) if exc.detail else "HTTP error.",
                    "details": {},
                },
                "request_id": request_id,
            },
            headers={REQUEST_ID_HEADER: request_id} if request_id else None,
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "")
        log = get_logger(__name__)
        log.error(
            "unhandled_exception",
            request_id=request_id,
            path=request.url.path,
            error=exc.__class__.__name__,
        )
        # Never leak internal exception details to the client.
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred.",
                    "details": {},
                },
                "request_id": request_id,
            },
            headers={REQUEST_ID_HEADER: request_id} if request_id else None,
        )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and return the FastAPI application."""
    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=__app_name__,
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.state.settings = settings

    _register_middlewares(app, settings)
    _register_exception_handlers(app)

    app.include_router(api_v1_router, prefix=API_V1_PREFIX)

    @app.get("/", include_in_schema=False)
    async def _root() -> dict[str, str]:
        return {
            "name": __app_name__,
            "version": __version__,
            "docs": "/docs",
            "health": f"{API_V1_PREFIX}/health",
        }

    return app


# Expose a module-level app for `uvicorn app.main:app`
app = create_app()