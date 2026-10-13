import { apiClient } from "@/services/apiClient";
import type { HistoryListResponse, HistorySummary } from "@/types/history";

export const historyApi = {
  list: (
    opts: {
      objectType?: string;
      status?: string;
      connectionId?: number;
      limit?: number;
      offset?: number;
    } = {},
  ): Promise<HistoryListResponse> => {
    const params = new URLSearchParams();
    if (opts.objectType) params.set("object_type", opts.objectType);
    if (opts.status) params.set("status", opts.status);
    if (opts.connectionId) {
      params.set("connection_id", String(opts.connectionId));
    }
    if (opts.limit) params.set("limit", String(opts.limit));
    if (opts.offset) params.set("offset", String(opts.offset));
    const qs = params.toString();
    return apiClient.get<HistoryListResponse>(
      `/api/v1/history${qs ? `?${qs}` : ""}`,
    );
  },

  summary: (): Promise<HistorySummary> =>
    apiClient.get<HistorySummary>("/api/v1/history/summary"),
};