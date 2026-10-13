"""Content service: create and update WordPress posts/pages.

Orchestrates:
  - WordPress REST create/update
  - Optional Rank Math meta write via companion plugin
  - Publish history recording
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import OperationType
from app.config.logging import get_logger
from app.config.settings import Settings
from app.core.exceptions import AppError, AuthError, ValidationError
from app.core.http_client import SafeHttpClient
from app.integrations.rankmath.client import RankMathClient
from app.integrations.rankmath.exceptions import (
    RankMathCompanionMissingError,
    RankMathError,
    RankMathInactiveError,
)
from app.integrations.rankmath.types import RankMathMeta
from app.integrations.wordpress.auth import build_auth_headers
from app.integrations.wordpress.client import WordPressClient
from app.integrations.wordpress.types import WPPost
from app.models.connection import Connection
from app.models.publish_history import PublishHistory
from app.schemas.content import (
    ContentCreateRequest,
    ContentGetResponse,
    ContentPublishResponse,
    ContentUpdateRequest,
)
from app.security import secrets as secret_store

_log = get_logger(__name__)


REST_PATH_BY_KIND: dict[str, str] = {
    "post": "posts",
    "page": "pages",
}


class ContentService:
    """Stateless service. Construct per request."""

    def __init__(self, *, settings: Settings, session: AsyncSession) -> None:
        self._settings = settings
        self._session = session

    # --- Create ------------------------------------------------------------

    async def create(
        self,
        payload: ContentCreateRequest,
        *,
        http: SafeHttpClient,
    ) -> ContentPublishResponse:
        connection = await self._require_connection(payload.connection_id)
        wp, rm_auth_headers = await self._clients(connection, http)
        rest_path = REST_PATH_BY_KIND[payload.kind]

        wp_payload = self._build_wp_payload_create(payload)
        warnings: list[str] = []

        try:
            wp_post = await wp.create_post(wp_payload, post_type=rest_path)
        except AppError as exc:
            await self._record_history(
                connection_id=connection.id,
                object_type=payload.kind,
                wp_object_id=None,
                permalink=None,
                operation=OperationType.CREATE.value,
                status="failed",
                message=exc.message,
            )
            raise

        return await self._finalize(
            connection=connection,
            wp_post=wp_post,
            kind=payload.kind,
            rank_math=payload.rank_math,
            rank_math_auth_headers=rm_auth_headers,
            http=http,
            warnings=warnings,
            is_create=True,
        )

    # --- Update ------------------------------------------------------------

    async def update(
        self,
        *,
        kind: str,
        wp_object_id: int,
        payload: ContentUpdateRequest,
        http: SafeHttpClient,
    ) -> ContentPublishResponse:
        connection = await self._require_connection(payload.connection_id)
        wp, rm_auth_headers = await self._clients(connection, http)
        rest_path = REST_PATH_BY_KIND[kind]

        wp_payload = self._build_wp_payload_update(payload)
        warnings: list[str] = []

        try:
            wp_post = await wp.update_post(
                wp_object_id,
                wp_payload,
                post_type=rest_path,
            )
        except AppError as exc:
            await self._record_history(
                connection_id=connection.id,
                object_type=kind,
                wp_object_id=wp_object_id,
                permalink=None,
                operation=OperationType.UPDATE.value,
                status="failed",
                message=exc.message,
            )
            raise

        return await self._finalize(
            connection=connection,
            wp_post=wp_post,
            kind=kind,
            rank_math=payload.rank_math,
            rank_math_auth_headers=rm_auth_headers,
            http=http,
            warnings=warnings,
            is_create=False,
        )

    # --- Get ---------------------------------------------------------------

    async def get(
        self,
        *,
        kind: str,
        wp_object_id: int,
        connection_id: int,
        http: SafeHttpClient,
    ) -> ContentGetResponse:
        connection = await self._require_connection(connection_id)
        wp, rm_auth_headers = await self._clients(connection, http)
        rest_path = REST_PATH_BY_KIND[kind]

        wp_post = await wp.get_post(wp_object_id, post_type=rest_path)

        rank_math: RankMathMeta | None = None
        rank_math_available = False
        rank_math_reason: str | None = None

        rm = RankMathClient(
            base_url=connection.base_url,
            auth_headers=rm_auth_headers,
            http=http,
        )
        try:
            rank_math = await rm.get_meta(wp_post.id)
            rank_math_available = True
        except RankMathCompanionMissingError:
            rank_math_reason = "Companion plugin is not installed or not active."
        except RankMathInactiveError:
            rank_math_reason = "Rank Math is not active on this site."
        except RankMathError as exc:
            rank_math_reason = f"Rank Math error: {exc.message}"

        return ContentGetResponse(
            id=wp_post.id,
            kind=kind,  # type: ignore[arg-type]
            status=wp_post.status,
            slug=wp_post.slug,
            permalink=wp_post.link,
            title=wp_post.raw_title(),
            content=wp_post.raw_content(),
            excerpt=wp_post.raw_excerpt(),
            author_id=wp_post.author,
            featured_media_id=wp_post.featured_media,
            parent_id=wp_post.parent,
            menu_order=wp_post.menu_order,
            comment_status=wp_post.comment_status,
            ping_status=wp_post.ping_status,
            categories=list(wp_post.categories),
            tags=list(wp_post.tags),
            date=wp_post.date,
            modified=wp_post.modified,
            rank_math=rank_math,
            rank_math_available=rank_math_available,
            rank_math_reason=rank_math_reason,
        )

    # --- Internals ---------------------------------------------------------

    async def _finalize(
        self,
        *,
        connection: Connection,
        wp_post: WPPost,
        kind: str,
        rank_math: RankMathMeta | None,
        rank_math_auth_headers: dict[str, str],
        http: SafeHttpClient,
        warnings: list[str],
        is_create: bool,
    ) -> ContentPublishResponse:
        rank_math_written = False
        rank_math_error: str | None = None

        if rank_math is not None and rank_math.provided_fields():
            rm = RankMathClient(
                base_url=connection.base_url,
                auth_headers=rank_math_auth_headers,
                http=http,
            )
            try:
                await rm.set_meta(wp_post.id, rank_math)
                rank_math_written = True
            except RankMathCompanionMissingError:
                rank_math_error = (
                    "Companion plugin is not installed or not active; "
                    "Rank Math meta was not written."
                )
                warnings.append(rank_math_error)
            except RankMathInactiveError:
                rank_math_error = (
                    "Rank Math is not active on this site; "
                    "meta was not written."
                )
                warnings.append(rank_math_error)
            except RankMathError as exc:
                rank_math_error = f"Rank Math write failed: {exc.message}"
                warnings.append(rank_math_error)

        partial = (
            rank_math is not None
            and not rank_math_written
            and rank_math_error is not None
        )
        operation = OperationType.CREATE.value if is_create else OperationType.UPDATE.value
        status_str = "partial" if partial else "success"

        await self._record_history(
            connection_id=connection.id,
            object_type=kind,
            wp_object_id=wp_post.id,
            permalink=wp_post.link or None,
            operation=operation,
            status=status_str,
            message=rank_math_error,
        )

        message = (
            f"{kind.capitalize()} saved (ID {wp_post.id}, status {wp_post.status})."
            if not partial
            else (
                f"{kind.capitalize()} saved (ID {wp_post.id}) but Rank Math meta "
                f"could not be written: {rank_math_error}"
            )
        )

        return ContentPublishResponse(
            success=True,
            partial=partial,
            wp_object_id=wp_post.id,
            wp_object_type=kind,  # type: ignore[arg-type]
            permalink=wp_post.link or None,
            status=wp_post.status,
            title=wp_post.raw_title(),
            slug=wp_post.slug,
            rank_math_written=rank_math_written,
            rank_math_error=rank_math_error,
            message=message,
            warnings=warnings,
        )

    @staticmethod
    def _build_wp_payload_create(payload: ContentCreateRequest) -> dict[str, Any]:
        wp: dict[str, Any] = {
            "title": payload.title,
            "content": payload.content,
            "status": payload.status,
        }
        if payload.slug:
            wp["slug"] = payload.slug
        if payload.excerpt:
            wp["excerpt"] = payload.excerpt
        if payload.scheduled_date and payload.status == "future":
            wp["date"] = payload.scheduled_date
        if payload.author_id is not None:
            wp["author"] = payload.author_id
        if payload.featured_media_id is not None:
            wp["featured_media"] = payload.featured_media_id
        if payload.categories and payload.kind == "post":
            wp["categories"] = payload.categories
        if payload.tags and payload.kind == "post":
            wp["tags"] = payload.tags
        if payload.parent_id is not None and payload.kind == "page":
            wp["parent"] = payload.parent_id
        if payload.menu_order:
            wp["menu_order"] = payload.menu_order
        if payload.comment_status:
            wp["comment_status"] = payload.comment_status
        if payload.ping_status:
            wp["ping_status"] = payload.ping_status
        return wp

    @staticmethod
    def _build_wp_payload_update(payload: ContentUpdateRequest) -> dict[str, Any]:
        wp: dict[str, Any] = {}
        if payload.title is not None:
            wp["title"] = payload.title
        if payload.slug is not None:
            wp["slug"] = payload.slug
        if payload.content is not None:
            wp["content"] = payload.content
        if payload.excerpt is not None:
            wp["excerpt"] = payload.excerpt
        if payload.status is not None:
            wp["status"] = payload.status
        if payload.scheduled_date is not None:
            wp["date"] = payload.scheduled_date
        if payload.featured_media_id is not None:
            wp["featured_media"] = payload.featured_media_id
        if payload.categories is not None:
            wp["categories"] = payload.categories
        if payload.tags is not None:
            wp["tags"] = payload.tags
        if payload.parent_id is not None:
            wp["parent"] = payload.parent_id
        if payload.menu_order is not None:
            wp["menu_order"] = payload.menu_order
        if payload.comment_status is not None:
            wp["comment_status"] = payload.comment_status
        if payload.ping_status is not None:
            wp["ping_status"] = payload.ping_status
        return wp

    async def _require_connection(self, connection_id: int) -> Connection:
        result = await self._session.execute(
            select(Connection).where(Connection.id == connection_id)
        )
        c = result.scalar_one_or_none()
        if c is None:
            raise ValidationError(
                "Connection not found.",
                details={"connection_id": connection_id},
            )
        return c

    async def _clients(
        self,
        connection: Connection,
        http: SafeHttpClient,
    ) -> tuple[WordPressClient, dict[str, str]]:
        label = connection.secret_ref or connection.label
        password = secret_store.get_secret(
            label,
            secret_store.FIELD_WP_APP_PASSWORD,
        )
        if not password:
            raise AuthError(
                "Stored WordPress credentials are missing from the OS keyring.",
                details={"label": label},
            )

        auth_headers = build_auth_headers(
            connection.auth_method,
            connection.username,
            password,
        )
        wp_client = WordPressClient(
            base_url=connection.base_url,
            username=connection.username,
            app_password=password,
            auth_method=connection.auth_method,
            http=http,
        )
        return wp_client, auth_headers

    async def _record_history(
        self,
        *,
        connection_id: int,
        object_type: str,
        wp_object_id: int | None,
        permalink: str | None,
        operation: str,
        status: str,
        message: str | None,
    ) -> None:
        history = PublishHistory(
            object_type=object_type,
            wp_object_id=wp_object_id,
            permalink=permalink,
            operation=operation,
            status=status,
            message=message,
            connection_id=connection_id,
        )
        self._session.add(history)
        try:
            await self._session.commit()
        except Exception as exc:  # noqa: BLE001
            await self._session.rollback()
            _log.warning(
                "publish_history_write_failed",
                error=exc.__class__.__name__,
            )