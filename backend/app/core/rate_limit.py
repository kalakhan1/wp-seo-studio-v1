"""In-memory token-bucket rate limiter, keyed per host.

Suitable for a single-process Phase 1 deployment. For multi-worker production
this will be replaced by Redis-backed limiting.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from app.config.constants import (
    DEFAULT_RATE_LIMIT_PER_HOST,
    DEFAULT_RATE_LIMIT_WINDOW_SECONDS,
)
from app.core.exceptions import RateLimitError


@dataclass
class _Bucket:
    capacity: float
    refill_per_second: float
    tokens: float = field(init=False)
    last_refill: float = field(init=False)

    def __post_init__(self) -> None:
        self.tokens = self.capacity
        self.last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        if elapsed <= 0:
            return
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_second)
        self.last_refill = now

    def try_consume(self, tokens: float = 1.0) -> bool:
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def time_until(self, tokens: float = 1.0) -> float:
        self._refill()
        if self.tokens >= tokens:
            return 0.0
        needed = tokens - self.tokens
        return needed / self.refill_per_second if self.refill_per_second > 0 else float("inf")


class HostRateLimiter:
    """Async-safe per-host token bucket."""

    def __init__(
        self,
        capacity: int = DEFAULT_RATE_LIMIT_PER_HOST,
        window_seconds: int = DEFAULT_RATE_LIMIT_WINDOW_SECONDS,
        *,
        max_wait_seconds: float = 5.0,
    ) -> None:
        if capacity <= 0 or window_seconds <= 0:
            raise ValueError("capacity and window_seconds must be positive")
        self._capacity = float(capacity)
        self._refill = float(capacity) / float(window_seconds)
        self._max_wait = max_wait_seconds
        self._buckets: dict[str, _Bucket] = {}
        self._lock = asyncio.Lock()

    async def _get_bucket(self, key: str) -> _Bucket:
        async with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = _Bucket(capacity=self._capacity, refill_per_second=self._refill)
                self._buckets[key] = bucket
            return bucket

    async def acquire(self, key: str, tokens: float = 1.0) -> None:
        """Wait for a token or raise RateLimitError if the wait would be too long."""
        if not key:
            key = "_default"
        bucket = await self._get_bucket(key)

        if bucket.try_consume(tokens):
            return

        wait_for = bucket.time_until(tokens)
        if wait_for > self._max_wait:
            raise RateLimitError(
                "Rate limit exceeded for host",
                details={"host": key, "retry_after_seconds": round(wait_for, 2)},
            )

        await asyncio.sleep(wait_for)
        if not bucket.try_consume(tokens):
            # Small race; retry once with minimal wait.
            await asyncio.sleep(0.05)
            if not bucket.try_consume(tokens):
                raise RateLimitError(
                    "Rate limit exceeded for host",
                    details={"host": key},
                )

    def reset(self) -> None:
        """Clear all buckets. Used by tests."""
        self._buckets.clear()