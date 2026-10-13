"""Safe async HTTP client.

Wraps httpx.AsyncClient with:
  - SSRF guard (initial URL and every redirect hop)
  - timeout
  - retry on transport errors and 5xx
  - response size cap
  - per-host rate limiting
  - structured logging

Redirects are followed manually so each hop is validated.

An optional `transport` can be injected for testing. In production it stays
None and httpx uses its default transport.
"""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from app import __version__
from app.config.settings import Settings
from app.core.exceptions import AppError, WPError
from app.core.rate_limit import HostRateLimiter
from app.security.ssrf_guard import assert_safe_url_async

_REDIRECT_STATUS = {301, 302, 303, 307, 308}
_RETRYABLE_STATUS = {500, 502, 503, 504}


class SafeHttpClient:
    """Async HTTP client with safety guards."""

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._timeout = httpx.Timeout(
            timeout=float(settings.http_timeout),
            connect=min(10.0, float(settings.http_timeout)),
        )
        self._client = httpx.AsyncClient(
            timeout=self._timeout,
            follow_redirects=False,
            headers={
                "User-Agent": f"WPSEOSControlStudio/{__version__}",
                "Accept": "application/json",
            },
            transport=transport,
        )
        self._rate_limiter = HostRateLimiter()
        self._max_bytes = int(settings.http_max_response_bytes)
        self._max_attempts = int(settings.http_max_retries) + 1

    # --- Lifecycle ---------------------------------------------------------

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "SafeHttpClient":
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    # --- Public API --------------------------------------------------------

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("DELETE", url, **kwargs)

    async def request(
        self,
        method: str,
        url: str,
        *,
        allow_private: bool = False,
        max_redirects: int = 5,
        **kwargs: Any,
    ) -> httpx.Response:
        """Send an HTTP request with safety guards and redirect validation."""
        current_url = url
        current_method = method
        hops = 0

        while True:
            await assert_safe_url_async(current_url, allow_private=allow_private)
            host = (urlparse(current_url).hostname or "").lower()
            await self._rate_limiter.acquire(host)

            response = await self._send_with_retry(current_method, current_url, **kwargs)
            self._enforce_size(response)

            if response.status_code in _REDIRECT_STATUS and hops < max_redirects:
                location = response.headers.get("location")
                if not location:
                    return response
                current_url = urljoin(current_url, location)
                hops += 1
                if response.status_code == 303 or (
                    response.status_code in (301, 302) and current_method == "POST"
                ):
                    current_method = "GET"
                    kwargs.pop("json", None)
                    kwargs.pop("data", None)
                    kwargs.pop("content", None)
                continue

            if response.status_code in _REDIRECT_STATUS and hops >= max_redirects:
                raise AppError(
                    "Too many redirects",
                    details={"url": url, "max_redirects": max_redirects},
                )

            return response

    # --- Internals ---------------------------------------------------------

    async def _send_with_retry(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        attempt = 0
        last_exc: Exception | None = None

        while attempt < self._max_attempts:
            attempt += 1
            try:
                response = await self._client.request(method, url, **kwargs)
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt >= self._max_attempts:
                    raise WPError(
                        "HTTP transport error after retries",
                        details={"url": url, "attempts": attempt, "error": exc.__class__.__name__},
                    ) from exc
                await asyncio.sleep(min(0.5 * (2 ** (attempt - 1)), 5.0))
                continue

            if response.status_code in _RETRYABLE_STATUS and attempt < self._max_attempts:
                await asyncio.sleep(min(0.5 * (2 ** (attempt - 1)), 5.0))
                continue

            return response

        if last_exc is not None:
            raise WPError(
                "HTTP request failed",
                details={"url": url, "error": last_exc.__class__.__name__},
            ) from last_exc
        raise AppError("HTTP request failed without response", details={"url": url})

    def _enforce_size(self, response: httpx.Response) -> None:
        content_length = response.headers.get("content-length")
        if content_length is not None:
            try:
                size = int(content_length)
            except ValueError:
                size = -1
            if size > self._max_bytes:
                raise AppError(
                    "Response exceeds maximum allowed size",
                    details={"content_length": size, "max_bytes": self._max_bytes},
                )

        body = response.content
        if body is not None and len(body) > self._max_bytes:
            raise AppError(
                "Response exceeds maximum allowed size",
                details={"size": len(body), "max_bytes": self._max_bytes},
            )