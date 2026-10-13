"""OpenAI adapter.

Uses the standard Chat Completions endpoint. Requires AI_API_KEY to be
set. Never logs the API key.
"""

from __future__ import annotations

import httpx

from app.config.logging import get_logger
from app.config.settings import Settings
from app.integrations.ai.base import AIProvider, GenerationResult

_log = get_logger(__name__)

DEFAULT_MODEL = "gpt-4o-mini"
API_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider(AIProvider):
    name = "openai"
    model = DEFAULT_MODEL

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._model = settings.ai_model or DEFAULT_MODEL

    def available(self) -> bool:
        return bool(self._settings.ai_api_key)

    def reason_unavailable(self) -> str:
        if not self._settings.ai_api_key:
            return "AI_API_KEY is not set in the environment."
        return ""

    async def generate(
        self, prompt: str, *, max_tokens: int = 2000
    ) -> GenerationResult:
        if not self.available():
            return GenerationResult(
                ok=False,
                provider=self.name,
                error=self.reason_unavailable(),
            )

        headers = {
            "Authorization": f"Bearer {self._settings.ai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a careful SEO assistant. Follow the user's "
                        "instructions exactly. When a fact is not provided, "
                        "return the literal string NEEDS_INPUT for that field. "
                        "Never invent ingredients, certifications, health "
                        "benefits, prices, or manufacturer details."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(API_URL, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            _log.warning("openai_request_failed", error=exc.__class__.__name__)
            return GenerationResult(
                ok=False,
                provider=self.name,
                model=self._model,
                error=f"Network error: {exc.__class__.__name__}",
            )

        if response.status_code in (401, 403):
            return GenerationResult(
                ok=False,
                provider=self.name,
                model=self._model,
                error="OpenAI rejected the API key.",
            )
        if response.status_code == 429:
            return GenerationResult(
                ok=False,
                provider=self.name,
                model=self._model,
                error="OpenAI rate limit reached. Try again later.",
            )
        if response.status_code >= 500:
            return GenerationResult(
                ok=False,
                provider=self.name,
                model=self._model,
                error="OpenAI server error.",
            )
        if response.status_code != 200:
            return GenerationResult(
                ok=False,
                provider=self.name,
                model=self._model,
                error=f"OpenAI returned HTTP {response.status_code}.",
            )

        try:
            data = response.json()
        except ValueError:
            return GenerationResult(
                ok=False,
                provider=self.name,
                model=self._model,
                error="OpenAI returned a non-JSON response.",
            )

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return GenerationResult(
                ok=False,
                provider=self.name,
                model=self._model,
                error="OpenAI response shape was unexpected.",
            )

        return GenerationResult(
            ok=True,
            provider=self.name,
            model=self._model,
            raw_response=str(content),
        )