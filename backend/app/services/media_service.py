"""Media service: upload, list, get, update, delete.

Orchestrates:
  - validation of uploaded files
  - content hashing (dedup within a connection)
  - WordPress upload/update/delete
  - local media_records cache

Media is uploaded to WordPress and cached locally. The local cache is
authoritative for search/list; WordPress is authoritative for the actual
file and public URL.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.core.exceptions import ValidationError
from app.core.http_client import SafeHttpClient
from app.integrations.wordpress.client import WordPressClient
from app.integrations.wordpress.exceptions import WPNotFoundError
from app.integrations.wordpress.types import WPMedia
from app.models.connection import Connection
from app.models.media_record import MediaRecord
from app.schemas.media import (
    MediaListResponse,
    MediaResponse,
    MediaUpdateRequest,
    MediaUploadResponse,
)
from app.security import secrets as secret_store
from app.security.upload_guard import validate_image_upload

_log = logging.getLogger(__name__)


class MediaService:
    """Stateless. Construct per request with settings + session."""

    def __init__(self, *, settings: Settings, session: AsyncSession) -> None:
        self._settings = settings
        self._session = session

    # --- Upload ------------------------------------------------------------

    async def upload(
        self,
        *,
        connection_id: int,
        filename: str,
        content: bytes,
        declared_mime: str | None,
        http: SafeHttpClient,
        title: str | None = None,
        alt_text: str | None = None,
        caption: str | None = None,
        description: str | None = None,
    ) -> MediaUploadResponse:
        connection = await self._require_connection(connection_id)
        validated = validate_image_upload(
            filename=filename,
            content=content,
            declared_mime=declared_mime,
        )

        content_hash = hashlib.sha256(validated.content).hexdigest()

        # Local dedup within the same connection: if identical bytes are
        # already cached, reuse the WordPress media item.
        existing = await self._find_by_hash(connection_id, content_hash)
        if existing is not None and existing.wp_media_id:
            _log.info(
                "media_upload_deduped",
                connection_id=connection_id,
                existing_id=existing.id,
                wp_media_id=existing.wp_media_id,
            )
            return MediaUploadResponse(
                media=self._to_response(existing),
                wordpress_id=existing.wp_media_id,
                wordpress_url=existing.url or "",
            )

        wp_client = await self._wp_client(connection, http)
        wp_media = await wp_client.upload_media(
            filename=validated.filename,
            content=validated.content,
            mime_type=validated.mime_type,
            title=title,
            alt_text=alt_text,
            caption=caption,
            description=description,
        )

        record = MediaRecord(
            wp_media_id=wp_media.id,
            filename=validated.filename,
            url=wp_media.source_url,
            mime=wp_media.mime_type or validated.mime_type,
            size_bytes=validated.size_bytes,
            width=wp_media.width(),
            height=wp_media.height(),
            alt_text=alt_text if alt_text is not None else wp_media.alt_text,
            title=title if title is not None else wp_media.rendered_title(),
            caption=caption if caption is not None else wp_media.rendered_caption(),
            description=(
                description if description is not None else wp_media.rendered_description()
            ),
            content_hash=content_hash,
            connection_id=connection_id,
        )
        self._session.add(record)
        await self._session.commit()
        await self._session.refresh(record)

        return MediaUploadResponse(
            media=self._to_response(record),
            wordpress_id=wp_media.id,
            wordpress_url=wp_media.source_url,
        )

    # --- List / Get --------------------------------------------------------

    async def list_items(
        self,
        *,
        connection_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
        query: str | None = None,
    ) -> MediaListResponse:
        stmt = select(MediaRecord)
        count_stmt = select(func.count(MediaRecord.id))

        if connection_id is not None:
            stmt = stmt.where(MediaRecord.connection_id == connection_id)
            count_stmt = count_stmt.where(MediaRecord.connection_id == connection_id)

        if query:
            like = f"%{query}%"
            stmt = stmt.where(MediaRecord.filename.ilike(like))
            count_stmt = count_stmt.where(MediaRecord.filename.ilike(like))

        stmt = stmt.order_by(MediaRecord.id.desc()).limit(limit).offset(offset)

        result = await self._session.execute(stmt)
        rows: Iterable[MediaRecord] = result.scalars().all()

        total_result = await self._session.execute(count_stmt)
        total = int(total_result.scalar_one() or 0)

        return MediaListResponse(
            items=[self._to_response(r) for r in rows],
            total=total,
        )

    async def get(self, media_id: int) -> MediaResponse:
        record = await self._require_media(media_id)
        return self._to_response(record)

    # --- Update / Delete ---------------------------------------------------

    async def update(
        self,
        *,
        media_id: int,
        payload: MediaUpdateRequest,
        http: SafeHttpClient,
    ) -> MediaResponse:
        record = await self._require_media(media_id)

        if record.connection_id and payload.sync_to_wordpress and record.wp_media_id:
            connection = await self._require_connection(record.connection_id)
            wp_client = await self._wp_client(connection, http)
            wp_media = await wp_client.update_media(
                record.wp_media_id,
                title=payload.title,
                alt_text=payload.alt_text,
                caption=payload.caption,
                description=payload.description,
            )
            record.url = wp_media.source_url or record.url
            record.mime = wp_media.mime_type or record.mime
            record.width = wp_media.width() or record.width
            record.height = wp_media.height() or record.height

        if payload.title is not None:
            record.title = payload.title
        if payload.alt_text is not None:
            record.alt_text = payload.alt_text
        if payload.caption is not None:
            record.caption = payload.caption
        if payload.description is not None:
            record.description = payload.description

        await self._session.commit()
        await self._session.refresh(record)
        return self._to_response(record)

    async def delete(
        self,
        *,
        media_id: int,
        http: SafeHttpClient,
        force: bool = False,
    ) -> None:
        record = await self._require_media(media_id)
        if record.connection_id and record.wp_media_id:
            connection = await self._require_connection(record.connection_id)
            wp_client = await self._wp_client(connection, http)
            try:
                await wp_client.delete_media(record.wp_media_id, force=force)
            except WPNotFoundError:
                # Already gone on WordPress; continue with local delete.
                pass
        await self._session.delete(record)
        await self._session.commit()

    # --- Internals ---------------------------------------------------------

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

    async def _require_media(self, media_id: int) -> MediaRecord:
        result = await self._session.execute(
            select(MediaRecord).where(MediaRecord.id == media_id)
        )
        m = result.scalar_one_or_none()
        if m is None:
            raise ValidationError(
                "Media not found.",
                details={"media_id": media_id},
            )
        return m

    async def _find_by_hash(
        self,
        connection_id: int,
        content_hash: str,
    ) -> MediaRecord | None:
        result = await self._session.execute(
            select(MediaRecord)
            .where(MediaRecord.connection_id == connection_id)
            .where(MediaRecord.content_hash == content_hash)
        )
        return result.scalar_one_or_none()

    async def _wp_client(
        self,
        connection: Connection,
        http: SafeHttpClient,
    ) -> WordPressClient:
        label = connection.secret_ref or connection.label
        password = secret_store.get_secret(
            label,
            secret_store.FIELD_WP_APP_PASSWORD,
        )
        if not password:
            raise ValidationError(
                "Stored WordPress credentials are missing from the OS keyring.",
                details={"label": label},
            )
        return WordPressClient(
            base_url=connection.base_url,
            username=connection.username,
            app_password=password,
            auth_method=connection.auth_method,
            http=http,
        )

    @staticmethod
    def _to_response(record: MediaRecord) -> MediaResponse:
        return MediaResponse(
            id=record.id,
            wp_media_id=record.wp_media_id,
            filename=record.filename,
            url=record.url,
            mime=record.mime,
            size_bytes=record.size_bytes,
            width=record.width,
            height=record.height,
            alt_text=record.alt_text,
            title=record.title,
            caption=record.caption,
            description=record.description,
            content_hash=record.content_hash,
            created_at=record.created_at.isoformat(),
            updated_at=record.updated_at.isoformat(),
        )


# Ensure WPMedia is imported for type-checker awareness of the module.
_ = WPMedia