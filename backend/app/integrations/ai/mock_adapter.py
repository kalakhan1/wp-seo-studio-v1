"""Mock AI adapter.

Returns a deterministic sample JSON object so the studio can be tested
end-to-end without a real AI provider or API key.
"""

from __future__ import annotations

import json

from app.integrations.ai.base import AIProvider, GenerationResult

_MOCK_PRODUCT_JSON = {
    "product_name": "NEEDS_INPUT",
    "slug": "needs-input",
    "short_description": "NEEDS_INPUT",
    "full_description": "NEEDS_INPUT",
    "sku_placeholder": "NEEDS_INPUT",
    "category_suggestions": ["NEEDS_INPUT"],
    "tags": ["NEEDS_INPUT"],
    "attributes": [],
    "pricing_placeholder": {
        "regular_price": "NEEDS_INPUT",
        "sale_price": "NEEDS_INPUT",
    },
    "images": {
        "featured_filename": "needs-input.jpg",
        "featured_alt": "NEEDS_INPUT",
        "gallery_filenames": [],
    },
    "rank_math": {
        "seo_title": "NEEDS_INPUT",
        "meta_description": "NEEDS_INPUT",
        "focus_keyword": "NEEDS_INPUT",
        "secondary_keywords": [],
    },
    "internal_links": [],
    "related_products": [],
    "faq_suggestions": [],
    "notes": "This is a mock response from the mock AI adapter.",
}


_MOCK_BLOG_JSON = {
    "title": "NEEDS_INPUT",
    "slug": "needs-input",
    "excerpt": "NEEDS_INPUT",
    "outline": [
        {"heading": "NEEDS_INPUT", "level": 2, "summary": "NEEDS_INPUT"},
    ],
    "introduction": "NEEDS_INPUT",
    "sections": [],
    "conclusion": "NEEDS_INPUT",
    "rank_math": {
        "seo_title": "NEEDS_INPUT",
        "meta_description": "NEEDS_INPUT",
        "focus_keyword": "NEEDS_INPUT",
        "secondary_keywords": [],
    },
    "images": {
        "featured_filename": "needs-input.jpg",
        "featured_alt": "NEEDS_INPUT",
        "inline_concepts": [],
    },
    "internal_links": [],
    "related_products": [],
    "cta": "NEEDS_INPUT",
    "faq_suggestions": [],
    "notes": "This is a mock response from the mock AI adapter.",
}


class MockAIProvider(AIProvider):
    name = "mock"
    model = "mock-v1"

    def __init__(self, template_type: str | None = None) -> None:
        self._template_type = template_type

    def available(self) -> bool:
        return True

    def reason_unavailable(self) -> str:
        return ""

    async def generate(
        self, prompt: str, *, max_tokens: int = 2000
    ) -> GenerationResult:
        del max_tokens
        payload = _MOCK_PRODUCT_JSON
        if self._template_type == "blog":
            payload = _MOCK_BLOG_JSON
        elif self._template_type == "product":
            payload = _MOCK_PRODUCT_JSON

        text = json.dumps(payload, indent=2, ensure_ascii=False)
        return GenerationResult(
            ok=True,
            provider=self.name,
            model=self.model,
            raw_response=text,
            warnings=[
                "Mock provider used. Replace AI_PROVIDER in .env to use a real provider."
            ],
        )