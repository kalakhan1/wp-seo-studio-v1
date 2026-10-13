/**
 * Types mirroring backend/app/schemas/ai_prompt.py
 */

export type TemplateType = "product" | "blog";

export interface PromptTemplate {
  id: number;
  name: string;
  template_type: string;
  content: string;
  is_default: boolean;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface PromptTemplateList {
  items: PromptTemplate[];
}

export interface PromptUpdateRequest {
  content: string;
}

export interface PromptRestoreResponse {
  restored: boolean;
  template: PromptTemplate;
}

export interface AIGenerateRequest {
  prompt: string;
  template_type?: TemplateType;
}

export interface AIGenerateResponse {
  ok: boolean;
  provider: string;
  model: string;
  raw_response: string;
  parsed: Record<string, unknown> | unknown[] | null;
  parse_error: string;
  warnings: string[];
}

export interface AIStatusResponse {
  provider: string;
  available: boolean;
  model: string;
  reason: string;
}