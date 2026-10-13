"""Unit tests for app.core.rate_limit.HostRateLimiter."""

from __future__ import annotations

import pytest

from app.core.exceptions import RateLimitError
from app.core.rate_limit import HostRateLimiter


async def test_allows_up_to_capacity() -> None:
    limiter = HostRateLimiter(capacity=3, window_seconds=60, max_wait_seconds=0.01)
    for _ in range(3):
        await limiter.acquire("example.com")


async def test_raises_when_wait_exceeds_max() -> None:
    limiter = HostRateLimiter(capacity=1, window_seconds=60, max_wait_seconds=0.01)
    await limiter.acquire("example.com")
    with pytest.raises(RateLimitError):
        await limiter.acquire("example.com")


async def test_reset_clears_buckets() -> None:
    limiter = HostRateLimiter(capacity=1, window_seconds=60, max_wait_seconds=0.01)
    await limiter.acquire("example.com")
    limiter.reset()
    # After reset, capacity is available again
    await limiter.acquire("example.com")