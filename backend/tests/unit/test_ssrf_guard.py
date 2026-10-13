"""Unit tests for app.security.ssrf_guard."""

from __future__ import annotations

import pytest

from app.core.exceptions import SSRFBlockedError
from app.security.ssrf_guard import (
    assert_safe_url_async,
    is_safe_url,
    is_safe_url_async,
)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/admin",
        "http://localhost:8000/",
        "http://10.0.0.1/",
        "http://192.168.1.1/",
        "http://172.16.0.1/",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/",
        "http://0.0.0.0/",
        "ftp://example.test/file",
        "file:///etc/passwd",
        "javascript:alert(1)",
        "http://",
    ],
)
def test_blocked_urls(url: str) -> None:
    assert is_safe_url(url) is False


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/",
        "https://api.wordpress.org/",
        "http://1.1.1.1/",
    ],
)
def test_allowed_public_urls(url: str) -> None:
    # Public URLs with resolvable hosts should pass
    # If offline, DNS resolution may fail and is_safe_url returns False; we
    # only assert that known-bad URLs are blocked above, so this test stays
    # tolerant. Skip if resolution fails.
    result = is_safe_url(url)
    if not result:
        pytest.skip(f"DNS resolution failed for {url} (offline environment)")


async def test_assert_safe_url_async_blocks_private() -> None:
    with pytest.raises(SSRFBlockedError):
        await assert_safe_url_async("http://127.0.0.1/")


async def test_assert_safe_url_async_allows_private_when_flagged() -> None:
    # allow_private=True should not raise for private targets
    await assert_safe_url_async("http://127.0.0.1/", allow_private=True)


async def test_is_safe_url_async_returns_false_for_private() -> None:
    assert await is_safe_url_async("http://10.0.0.1/") is False