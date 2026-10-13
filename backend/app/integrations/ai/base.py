"""AI provider interface.

Every adapter must return a GenerationResult. Adapters should never raise
on provider failure — they return a result with `ok=False` so the caller
can surface a truthful message.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class GenerationResult:
    ok: bool
    provider: str
    model: str = ""
    raw_response: str = ""
    error: str = ""
    warnings: list[str] = field(default_factory=list)


class AIProvider(ABC):
    """Common interface for all AI provider adapters."""

    name: str = "unknown"
    model: str = ""

    @abstractmethod
    async def generate(self, prompt: str, *, max_tokens: int = 2000) -> GenerationResult:
        """Send a prompt, return the raw response text."""

    @abstractmethod
    def available(self) -> bool:
        """Whether the provider is configured and ready."""

    @abstractmethod
    def reason_unavailable(self) -> str:
        """Human-readable reason when `available()` is False."""