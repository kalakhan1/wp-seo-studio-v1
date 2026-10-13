/**
 * SEO audit API wrappers.
 */

import { apiClient } from "@/services/apiClient";
import type {
  AuditHistoryResponse,
  AuditReportResponse,
} from "@/types/seoAudit";

export const seoAuditApi = {
  run: (connectionId: number): Promise<AuditReportResponse> =>
    apiClient.post<AuditReportResponse>(
      `/api/v1/seo-audit/run?connection_id=${connectionId}`,
      {},
    ),

  history: (
    connectionId?: number,
    limit = 20,
  ): Promise<AuditHistoryResponse> => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (connectionId !== undefined) {
      params.set("connection_id", String(connectionId));
    }
    return apiClient.get<AuditHistoryResponse>(
      `/api/v1/seo-audit/history?${params.toString()}`,
    );
  },
};