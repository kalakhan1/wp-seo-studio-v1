import { apiClient } from "@/services/apiClient";
import type {
  QueueJob,
  QueueListResponse,
  QueueSummary,
} from "@/types/queue";

export const queueApi = {
  list: (
    opts: {
      status?: string;
      jobType?: string;
      connectionId?: number;
      limit?: number;
    } = {},
  ): Promise<QueueListResponse> => {
    const params = new URLSearchParams();
    if (opts.status) params.set("status", opts.status);
    if (opts.jobType) params.set("job_type", opts.jobType);
    if (opts.connectionId) params.set("connection_id", String(opts.connectionId));
    if (opts.limit) params.set("limit", String(opts.limit));
    const qs = params.toString();
    return apiClient.get<QueueListResponse>(`/api/v1/queue${qs ? `?${qs}` : ""}`);
  },

  summary: (): Promise<QueueSummary> =>
    apiClient.get<QueueSummary>("/api/v1/queue/summary"),

  get: (id: number): Promise<QueueJob> =>
    apiClient.get<QueueJob>(`/api/v1/queue/${id}`),

  cancel: (id: number): Promise<QueueJob> =>
    apiClient.post<QueueJob>(`/api/v1/queue/${id}/cancel`, {}),

  retry: (id: number): Promise<QueueJob> =>
    apiClient.post<QueueJob>(`/api/v1/queue/${id}/retry`, {}),
};