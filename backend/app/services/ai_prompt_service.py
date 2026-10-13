"""AI prompt service.

Manages prompt templates (product + blog) and, optionally, sends prompts
to a configured AI provider. The mock provider is the default, so the
studio is fully usable without any API key.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging import get_logger
from app.config.settings import Settings
from app.core.exceptions import ValidationError
from app.integrations.ai.factory import get_provider
from app.models.prompt_template import PromptTemplate
from app.schemas.ai_prompt import (
    AIGenerateResponse,
    AIStatusResponse,
    PromptRestoreResponse,
    PromptTemplateListResponse,
    PromptTemplateResponse,
)
from app.utils.json_safe import extract_json_block

_log = get_logger(__name__)


PRODUCT_DEFAULT_PROMPT = """\
You are generating structured content for a WooCommerce product.

Return ONLY a single JSON object matching this schema. Use the literal
string "NEEDS_INPUT" for any field whose value is not provided by the
user or is not a verifiable fact.

Never invent:
  - ingredients
  - certifications
  - manufacturer details
  - health benefits or medical claims
  - dosage
  - prices or availability
  - safety assurances
  - product facts

Schema:
{
  "product_name": "string | NEEDS_INPUT",
  "slug": "url-slug-or-needs-input",
  "short_description": "string | NEEDS_INPUT",
  "full_description": "string | NEEDS_INPUT",
  "sku_placeholder": "string | NEEDS_INPUT",
  "category_suggestions": ["string"],
  "subcategory_suggestions": ["string"],
  "brand": "string | NEEDS_INPUT",
  "tags": ["string"],
  "attributes": [{"name": "string", "value": "NEEDS_INPUT"}],
  "pricing_placeholder": {
    "regular_price": "NEEDS_INPUT",
    "sale_price": "NEEDS_INPUT"
  },
  "images": {
    "featured_filename": "lowercase-with-hyphens.jpg",
    "featured_alt": "string",
    "featured_title": "string",
    "featured_caption": "string",
    "gallery_filenames": ["lowercase-with-hyphens.jpg"]
  },
  "rank_math": {
    "seo_title": "50-60 characters, unique",
    "meta_description": "150-160 characters",
    "focus_keyword": "single primary keyword",
    "secondary_keywords": ["string"],
    "canonical_url": "string | NEEDS_INPUT"
  },
  "internal_links": [{"anchor": "string", "suggestion": "topic to link to"}],
  "related_products": ["string"],
  "faq_suggestions": [{"question": "string", "answer": "string | NEEDS_INPUT"}],
  "schema_relevant_facts": {
    "category": "string | NEEDS_INPUT",
    "brand": "string | NEEDS_INPUT",
    "sku": "NEEDS_INPUT"
  }
}

Product details provided by the user:
- Name: {product_name}
- Category: {category}
- Short facts: {facts}

Return ONLY the JSON object. No commentary. No markdown fences.
"""


BLOG_DEFAULT_PROMPT = """\
You are writing a helpful, original blog article for a WooCommerce store.

Requirements:
  - Accurate information only. No fabricated citations.
  - No copied competitor text.
  - No keyword stuffing.
  - Natural use of the primary keyword.
  - Distinguish traditional use from established scientific evidence.
  - Recommend consulting a professional where appropriate.
  - Use a clear H1/H2/H3 structure.

Return ONLY a single JSON object matching this schema. Use the literal
string "NEEDS_INPUT" for any field whose value is not provided or is not
verifiable.

Schema:
{
  "title": "string",
  "slug": "url-slug",
  "excerpt": "1-2 sentence summary",
  "search_intent": "informational | transactional | navigational",
  "target_audience": "string",
  "primary_keyword": "string",
  "secondary_keywords": ["string"],
  "outline": [
    {"level": 2, "heading": "string", "summary": "string"}
  ],
  "introduction": "string",
  "sections": [
    {"heading": "string", "body": "string"}
  ],
  "conclusion": "string",
  "rank_math": {
    "seo_title": "50-60 characters, unique",
    "meta_description": "150-160 characters",
    "focus_keyword": "string",
    "secondary_keywords": ["string"]
  },
  "images": {
    "featured_filename": "lowercase-with-hyphens.jpg",
    "featured_alt": "string",
    "featured_caption": "string",
    "inline_concepts": ["string"]
  },
  "internal_links": [{"anchor": "string", "suggestion": "topic"}],
  "related_products": ["string"],
  "cta": "string",
  "faq_suggestions": [{"question": "string", "answer": "string"}]
}

Article details provided by the user:
- Topic: {topic}
- Audience: {audience}
- Primary keyword: {primary_keyword}

Return ONLY the JSON object. No commentary. No markdown fences.
"""


class AIPromptService:
    """Stateless. Construct per request with settings + session."""

    def __init__(self, *, settings: Settings, session: AsyncSession) -> None:
        self._settings = settings
        self._session = session

    # --- Status ------------------------------------------------------------

    async def status(self) -> AIStatusResponse:
        provider_name = (self._settings.ai_provider or "none").strip().lower()
        provider = get_provider(self._settings)
        return AIStatusResponse(
            provider=provider.name if provider.available() else provider_name,
            available=provider.available(),
            model=provider.model,
            reason=provider.reason_unavailable(),
        )

    # --- Templates ---------------------------------------------------------

    async def list_templates(self) -> PromptTemplateListResponse:
        await self._ensure_defaults()
        result = await self._session.execute(
            select(PromptTemplate).order_by(PromptTemplate.template_type.asc())
        )
        rows = result.scalars().all()
        return PromptTemplateListResponse(
            items=[self._to_response(r) for r in rows]
        )

    async def get_template(self, template_type: str) -> PromptTemplateResponse:
        await self._ensure_defaults()
        row = await self._require_template(template_type)
        return self._to_response(row)

    async def update_template(
        self, template_type: str, content: str
    ) -> PromptTemplateResponse:
        await self._ensure_defaults()
        row = await self._require_template(template_type)
        row.content = content
        row.is_default = False
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_response(row)

    async def restore_default(self, template_type: str) -> PromptRestoreResponse:
        default = self._default_for(template_type)
        await self._ensure_defaults()
        row = await self._require_template(template_type)
        row.content = default
        row.is_default = True
        await self._session.commit()
        await self._session.refresh(row)
        return PromptRestoreResponse(
            restored=True,
            template=self._to_response(row),
        )

    # --- Generate ----------------------------------------------------------

    async def generate(
        self,
        *,
        prompt: str,
        template_type: str | None,
        max_tokens: int = 2000,
    ) -> AIGenerateResponse:
        provider = get_provider(self._settings, template_type=template_type)
        if not provider.available():
            return AIGenerateResponse(
                ok=False,
                provider=provider.name,
                reason="",  # type: ignore[arg-type]
                warnings=[provider.reason_unavailable()],
                parse_error="",
                raw_response="",
                parsed=None,
                model="",
            )

        result = await provider.generate(prompt, max_tokens=max_tokens)
        if not result.ok:
            return AIGenerateResponse(
                ok=False,
                provider=result.provider,
                model=result.model,
                raw_response="",
                parsed=None,
                parse_error=result.error,
                warnings=result.warnings,
            )

        parsed = extract_json_block(result.raw_response)
        parse_error = ""
        warnings = list(result.warnings)
        if parsed is None:
            parse_error = (
                "Could not parse a JSON object from the AI response. "
                "You can still copy and use the raw text below."
            )

        return AIGenerateResponse(
            ok=True,
            provider=result.provider,
            model=result.model,
            raw_response=result.raw_response,
            parsed=parsed if isinstance(parsed, (dict, list)) else None,
            parse_error=parse_error,
            warnings=warnings,
        )

    # --- Internals ---------------------------------------------------------

    @staticmethod
    def _default_for(template_type: str) -> str:
        if template_type == "product":
            return PRODUCT_DEFAULT_PROMPT
        if template_type == "blog":
            return BLOG_DEFAULT_PROMPT
        raise ValidationError(
            f"Unknown template type: {template_type!r}.",
            details={"allowed": ["product", "blog"]},
        )

    async def _ensure_defaults(self) -> None:
        """Seed both default templates on first use."""
        for template_type in ("product", "blog"):
            result = await self._session.execute(
                select(PromptTemplate).where(
                    PromptTemplate.template_type == template_type
                )
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                self._session.add(
                    PromptTemplate(
                        name=f"Default {template_type.title()} Prompt",
                        template_type=template_type,
                        content=self._default_for(template_type),
                        is_default=True,
                        description=(
                            "Shipped default. Restore this if you customize "
                            "and want to start over."
                        ),
                    )
                )
        await self._session.commit()

    async def _require_template(self, template_type: str) -> PromptTemplate:
        result = await self._session.execute(
            select(PromptTemplate).where(
                PromptTemplate.template_type == template_type
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise ValidationError(
                f"No template found for type {template_type!r}.",
                details={"template_type": template_type},
            )
        return row

    @staticmethod
    def _to_response(row: PromptTemplate) -> PromptTemplateResponse:
        return PromptTemplateResponse(
            id=row.id,
            name=row.name,
            template_type=row.template_type,
            content=row.content,
            is_default=row.is_default,
            description=row.description,
            created_at=row.created_at.isoformat(),
            updated_at=row.updated_at.isoformat(),
        )


# Ensure Any import is used (type-checker friendliness).