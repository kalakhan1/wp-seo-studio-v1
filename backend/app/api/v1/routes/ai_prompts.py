"""AI prompt studio endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DBSessionDep, SettingsDep
from app.schemas.ai_prompt import (
    AIGenerateRequest,
    AIGenerateResponse,
    AIStatusResponse,
    PromptRestoreResponse,
    PromptTemplateListResponse,
    PromptTemplateResponse,
    PromptUpdateRequest,
)
from app.services.ai_prompt_service import AIPromptService

router = APIRouter(prefix="/ai-prompts", tags=["ai-prompts"])


def _service(settings: SettingsDep, session: DBSessionDep) -> AIPromptService:
    return AIPromptService(settings=settings, session=session)


@router.get(
    "/status",
    response_model=AIStatusResponse,
    summary="AI provider readiness",
)
async def get_status(
    settings: SettingsDep,
    session: DBSessionDep,
) -> AIStatusResponse:
    return await _service(settings, session).status()


@router.get(
    "/templates",
    response_model=PromptTemplateListResponse,
    summary="List prompt templates",
)
async def list_templates(
    settings: SettingsDep,
    session: DBSessionDep,
) -> PromptTemplateListResponse:
    return await _service(settings, session).list_templates()


@router.get(
    "/templates/{template_type}",
    response_model=PromptTemplateResponse,
    summary="Get a prompt template",
)
async def get_template(
    template_type: str,
    settings: SettingsDep,
    session: DBSessionDep,
) -> PromptTemplateResponse:
    return await _service(settings, session).get_template(template_type)


@router.put(
    "/templates/{template_type}",
    response_model=PromptTemplateResponse,
    summary="Update a prompt template",
)
async def update_template(
    template_type: str,
    payload: PromptUpdateRequest,
    settings: SettingsDep,
    session: DBSessionDep,
) -> PromptTemplateResponse:
    return await _service(settings, session).update_template(
        template_type, payload.content
    )


@router.post(
    "/templates/{template_type}/restore",
    response_model=PromptRestoreResponse,
    summary="Restore a prompt template to its default",
)
async def restore_template(
    template_type: str,
    settings: SettingsDep,
    session: DBSessionDep,
) -> PromptRestoreResponse:
    return await _service(settings, session).restore_default(template_type)


@router.post(
    "/generate",
    response_model=AIGenerateResponse,
    summary="Send a prompt to the configured AI provider",
    description=(
        "Optional. When AI_PROVIDER is set to 'none' or 'mock', a "
        "deterministic mock response is returned so the studio can be "
        "tested without an external service."
    ),
)
async def generate(
    payload: AIGenerateRequest,
    settings: SettingsDep,
    session: DBSessionDep,
    max_tokens: int = Query(default=2000, ge=100, le=8000),
) -> AIGenerateResponse:
    return await _service(settings, session).generate(
        prompt=payload.prompt,
        template_type=payload.template_type,
        max_tokens=max_tokens,
    )