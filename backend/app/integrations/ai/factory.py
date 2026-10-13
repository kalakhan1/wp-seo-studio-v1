"""AI provider factory."""

from __future__ import annotations

from app.config.settings import Settings
from app.integrations.ai.base import AIProvider
from app.integrations.ai.mock_adapter import MockAIProvider
from app.integrations.ai.openai_adapter import OpenAIProvider


def get_provider(
    settings: Settings,
    *,
    template_type: str | None = None,
) -> AIProvider:
    """Return the configured provider. Falls back to mock when unset."""
    name = (settings.ai_provider or "none").strip().lower()

    if name == "openai":
        return OpenAIProvider(settings)

    if name == "mock":
        return MockAIProvider(template_type=template_type)

    # 'none' or unknown provider: use mock so the studio remains testable.
    return MockAIProvider(template_type=template_type)