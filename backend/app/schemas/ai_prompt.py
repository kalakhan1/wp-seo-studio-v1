"""Schemas for the AI prompt studio."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


TemplateType = Literal["product", "blog"]


class PromptTemplateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    template_type: str
    content: str
    is_default: bool
    description: str | None = None
    created_at: str
    updated_at: str


class PromptTemplateListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[PromptTemplateResponse] = Field(default_factory=list)


class PromptUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="New template body.",
    )


class PromptRestoreResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    restored: bool
    template: PromptTemplateResponse


class AIGenerateRequest(BaseModel):
    """Send a prompt to the configured AI provider."""

    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Full prompt text to send to the provider.",
    )
    template_type: TemplateType | None = Field(
        default=None,
        description="Optional hint for the response schema check.",
    )


class AIGenerateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    provider: str
    model: str = ""
    raw_response: str = ""
    parsed: dict | list | None = None
    parse_error: str = ""
    warnings: list[str] = Field(default_factory=list)


class AIStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    available: bool
    model: str = ""
    reason: str = ""