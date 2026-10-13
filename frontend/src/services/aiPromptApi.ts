/**
 * AI prompt studio API wrappers.
 */

import { apiClient } from "@/services/apiClient";
import type {
  AIGenerateResponse,
  AIStatusResponse,
  PromptRestoreResponse,
  PromptTemplate,
  PromptTemplateList,
  TemplateType,
} from "@/types/aiPrompt";

export const aiPromptApi = {
  status: (): Promise<AIStatusResponse> =>
    apiClient.get<AIStatusResponse>("/api/v1/ai-prompts/status"),

  listTemplates: (): Promise<PromptTemplateList> =>
    apiClient.get<PromptTemplateList>("/api/v1/ai-prompts/templates"),

  getTemplate: (type: TemplateType): Promise<PromptTemplate> =>
    apiClient.get<PromptTemplate>(`/api/v1/ai-prompts/templates/${type}`),

  updateTemplate: (
    type: TemplateType,
    content: string,
  ): Promise<PromptTemplate> =>
    apiClient.put<PromptTemplate>(
      `/api/v1/ai-prompts/templates/${type}`,
      { content },
    ),

  restoreTemplate: (type: TemplateType): Promise<PromptRestoreResponse> =>
    apiClient.post<PromptRestoreResponse>(
      `/api/v1/ai-prompts/templates/${type}/restore`,
      {},
    ),

  generate: (
    prompt: string,
    templateType?: TemplateType,
  ): Promise<AIGenerateResponse> =>
    apiClient.post<AIGenerateResponse>("/api/v1/ai-prompts/generate", {
      prompt,
      template_type: templateType,
    }),
};