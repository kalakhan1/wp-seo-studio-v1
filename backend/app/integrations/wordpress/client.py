"""WordPress REST API client.

Composes SafeHttpClient with WordPress authentication. All requests go
through the safe HTTP client so timeouts, retries, size caps, rate
limiting, and structured logging behave consistently with the rest of
the app.

Security note: `allow_private_hosts=True` is used because the base URL
comes from a user-configured connection profile, not from untrusted
input. Media URL fetching later will use strict SSRF checks.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.config.constants import AuthMethod
from app.core.http_client import SafeHttpClient
from app.integrations.wordpress.auth import build_auth_headers
from app.integrations.wordpress.exceptions import (
    WPAuthError,
    WPConnectionError,
    WPNotFoundError,
    WPResponseError,
)
from app.integrations.wordpress.types import (
    PostType,
    SiteInfo,
    Taxonomy,
    WPCategory,
    WPMedia,
    WPPost,
    WPTag,
    WPUser,
)


class WordPressClient:
    """Client for a single WordPress site.

    Construct per-request. The client is stateless apart from the base URL
    and precomputed auth headers.
    """

    def __init__(
        self,
        *,
        base_url: str,
        username: str,
        app_password: str,
        http: SafeHttpClient,
        auth_method: str = AuthMethod.APPLICATION_PASSWORD.value,
        allow_private_hosts: bool = True,
    ) -> None:
        if not base_url:
            raise WPAuthError("WordPress base URL is required.")
        self.base_url = base_url.rstrip("/")
        self._http = http
        self._allow_private = allow_private_hosts
        self._auth_headers = build_auth_headers(
            auth_method,
            username,
            app_password,
        )

    # --- Site & users ------------------------------------------------------

    async def get_site_info(self) -> SiteInfo:
        data = await self._get_json("/wp-json")
        return SiteInfo.model_validate(data)

    async def get_current_user(self) -> WPUser:
        data = await self._get_json(
            "/wp-json/wp/v2/users/me",
            params={"context": "edit"},
        )
        return WPUser.model_validate(data)

    # --- Types & taxonomies ------------------------------------------------

    async def list_post_types(self) -> list[PostType]:
        data = await self._get_json("/wp-json/wp/v2/types")
        if not isinstance(data, dict):
            return []
        return [PostType.model_validate(v) for v in data.values()]

    async def list_taxonomies(self) -> list[Taxonomy]:
        data = await self._get_json("/wp-json/wp/v2/taxonomies")
        if not isinstance(data, dict):
            return []
        return [Taxonomy.model_validate(v) for v in data.values()]

    async def list_categories(
        self,
        *,
        per_page: int = 100,
        page: int = 1,
        search: str | None = None,
    ) -> list[WPCategory]:
        params: dict[str, Any] = {"per_page": per_page, "page": page}
        if search:
            params["search"] = search
        data = await self._get_json("/wp-json/wp/v2/categories", params=params)
        if not isinstance(data, list):
            return []
        return [WPCategory.model_validate(item) for item in data]

    async def list_tags(
        self,
        *,
        per_page: int = 100,
        page: int = 1,
        search: str | None = None,
    ) -> list[WPTag]:
        params: dict[str, Any] = {"per_page": per_page, "page": page}
        if search:
            params["search"] = search
        data = await self._get_json("/wp-json/wp/v2/tags", params=params)
        if not isinstance(data, list):
            return []
        return [WPTag.model_validate(item) for item in data]

    # --- Posts -------------------------------------------------------------

    async def create_post(
        self,
        payload: dict[str, Any],
        *,
        post_type: str = "posts",
    ) -> WPPost:
        url = f"{self.base_url}/wp-json/wp/v2/{post_type}"
        data = await self._request_json("POST", url, json=payload)
        return WPPost.model_validate(data)

    async def update_post(
        self,
        post_id: int,
        payload: dict[str, Any],
        *,
        post_type: str = "posts",
    ) -> WPPost:
        url = f"{self.base_url}/wp-json/wp/v2/{post_type}/{post_id}"
        data = await self._request_json("POST", url, json=payload)
        return WPPost.model_validate(data)

    async def get_post(self, post_id: int, *, post_type: str = "posts") -> WPPost:
        url = f"{self.base_url}/wp-json/wp/v2/{post_type}/{post_id}"
        data = await self._get_json(f"/wp-json/wp/v2/{post_type}/{post_id}")
        return WPPost.model_validate(data)

    async def delete_post(
        self,
        post_id: int,
        *,
        post_type: str = "posts",
        force: bool = False,
    ) -> None:
        url = f"{self.base_url}/wp-json/wp/v2/{post_type}/{post_id}"
        params = {"force": "true"} if force else None
        try:
            response = await self._http.request(
                "DELETE",
                url,
                headers=self._auth_headers,
                params=params,
                allow_private=self._allow_private,
            )
        except httpx.HTTPError as exc:
            raise WPConnectionError(
                "Could not reach WordPress during post delete.",
                details={"url": url, "error": exc.__class__.__name__},
            ) from exc
        self._raise_for_status(response, url)

    # --- Media -------------------------------------------------------------

    async def list_media(self, *, per_page: int = 5, page: int = 1) -> list[WPMedia]:
        data = await self._get_json(
            "/wp-json/wp/v2/media",
            params={"per_page": per_page, "page": page},
        )
        if not isinstance(data, list):
            return []
        return [WPMedia.model_validate(item) for item in data]

    async def get_media(self, media_id: int) -> WPMedia:
        data = await self._get_json(f"/wp-json/wp/v2/media/{media_id}")
        return WPMedia.model_validate(data)

    async def upload_media(
        self,
        *,
        filename: str,
        content: bytes,
        mime_type: str,
        title: str | None = None,
        alt_text: str | None = None,
        caption: str | None = None,
        description: str | None = None,
    ) -> WPMedia:
        url = f"{self.base_url}/wp-json/wp/v2/media"
        files = {"file": (filename, content, mime_type)}

        form: dict[str, str] = {}
        if title is not None:
            form["title"] = title
        if alt_text is not None:
            form["alt_text"] = alt_text
        if caption is not None:
            form["caption"] = caption
        if description is not None:
            form["description"] = description

        try:
            response = await self._http.request(
                "POST",
                url,
                headers=self._auth_headers,
                files=files,
                data=form or None,
                allow_private=self._allow_private,
            )
        except httpx.HTTPError as exc:
            raise WPConnectionError(
                "Could not reach WordPress during media upload.",
                details={"url": url, "error": exc.__class__.__name__},
            ) from exc

        self._raise_for_status(response, url)

        try:
            return WPMedia.model_validate(response.json())
        except ValueError as exc:
            raise WPResponseError(
                "WordPress returned a non-JSON response to media upload.",
                details={"url": url, "status": response.status_code},
            ) from exc

    async def update_media(
        self,
        media_id: int,
        *,
        title: str | None = None,
        alt_text: str | None = None,
        caption: str | None = None,
        description: str | None = None,
    ) -> WPMedia:
        url = f"{self.base_url}/wp-json/wp/v2/media/{media_id}"
        payload: dict[str, str] = {}
        if title is not None:
            payload["title"] = title
        if alt_text is not None:
            payload["alt_text"] = alt_text
        if caption is not None:
            payload["caption"] = caption
        if description is not None:
            payload["description"] = description

        try:
            response = await self._http.request(
                "POST",
                url,
                headers=self._auth_headers,
                json=payload,
                allow_private=self._allow_private,
            )
        except httpx.HTTPError as exc:
            raise WPConnectionError(
                "Could not reach WordPress during media update.",
                details={"url": url, "error": exc.__class__.__name__},
            ) from exc

        self._raise_for_status(response, url)

        try:
            return WPMedia.model_validate(response.json())
        except ValueError as exc:
            raise WPResponseError(
                "WordPress returned a non-JSON response to media update.",
                details={"url": url, "status": response.status_code},
            ) from exc

    async def delete_media(self, media_id: int, *, force: bool = False) -> None:
        url = f"{self.base_url}/wp-json/wp/v2/media/{media_id}"
        params = {"force": "true"} if force else None
        try:
            response = await self._http.request(
                "DELETE",
                url,
                headers=self._auth_headers,
                params=params,
                allow_private=self._allow_private,
            )
        except httpx.HTTPError as exc:
            raise WPConnectionError(
                "Could not reach WordPress during media delete.",
                details={"url": url, "error": exc.__class__.__name__},
            ) from exc
        self._raise_for_status(response, url)

    # --- Internals ---------------------------------------------------------

    async def _get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        try:
            response = await self._http.request(
                "GET",
                url,
                headers=self._auth_headers,
                params=params,
                allow_private=self._allow_private,
            )
        except httpx.HTTPError as exc:
            raise WPConnectionError(
                "Could not reach WordPress.",
                details={"url": url, "error": exc.__class__.__name__},
            ) from exc

        self._raise_for_status(response, url)

        try:
            return response.json()
        except ValueError as exc:
            raise WPResponseError(
                "WordPress returned a non-JSON response.",
                details={"url": url, "status": response.status_code},
            ) from exc

    async def _request_json(
        self,
        method: str,
        url: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> Any:
        try:
            response = await self._http.request(
                method,
                url,
                headers=self._auth_headers,
                json=json,
                allow_private=self._allow_private,
            )
        except httpx.HTTPError as exc:
            raise WPConnectionError(
                "Could not reach WordPress.",
                details={"url": url, "error": exc.__class__.__name__},
            ) from exc

        self._raise_for_status(response, url)

        try:
            return response.json()
        except ValueError as exc:
            raise WPResponseError(
                "WordPress returned a non-JSON response.",
                details={"url": url, "status": response.status_code},
            ) from exc

    @staticmethod
    def _raise_for_status(response: httpx.Response, url: str) -> None:
        if response.status_code in (200, 201, 202, 204):
            return
        if response.status_code in (401, 403):
            raise WPAuthError(
                "Authentication failed or insufficient permissions.",
                details={"url": url, "status": response.status_code},
            )
        if response.status_code == 404:
            raise WPNotFoundError(
                "WordPress REST endpoint not found.",
                details={"url": url, "status": response.status_code},
            )
        if response.status_code >= 500:
            raise WPResponseError(
                "WordPress returned a server error.",
                details={"url": url, "status": response.status_code},
            )
        # 400, 422 etc — include the WordPress error code if present.
        detail: dict[str, Any] = {"url": url, "status": response.status_code}
        try:
            body = response.json()
            if isinstance(body, dict):
                if "code" in body:
                    detail["wp_code"] = body["code"]
                if "message" in body:
                    detail["wp_message"] = body["message"]
        except Exception:  # noqa: BLE001
            pass
        raise WPResponseError(
            "WordPress rejected the request.",
            details=detail,
        )