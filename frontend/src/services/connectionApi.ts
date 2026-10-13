/**
 * Connection API wrappers. All responses are typed and never include secrets.
 */

import { apiClient } from "@/services/apiClient";
import type {
  Connection,
  ConnectionList,
  ConnectionSaveRequest,
  ConnectionTestRequest,
  ConnectionTestResponse,
} from "@/types/connection";
import type { CapabilityReport } from "@/types/capability";

export const connectionApi = {
  test: (payload: ConnectionTestRequest): Promise<ConnectionTestResponse> =>
    apiClient.post<ConnectionTestResponse>("/api/v1/connection/test", payload),

  save: (payload: ConnectionSaveRequest): Promise<Connection> =>
    apiClient.post<Connection>("/api/v1/connection", payload),

  list: (): Promise<ConnectionList> =>
    apiClient.get<ConnectionList>("/api/v1/connection"),

  get: (id: number): Promise<Connection> =>
    apiClient.get<Connection>(`/api/v1/connection/${id}`),

  remove: (id: number): Promise<void> =>
    apiClient.delete<void>(`/api/v1/connection/${id}`),

  verify: (id: number): Promise<ConnectionTestResponse> =>
    apiClient.post<ConnectionTestResponse>(`/api/v1/connection/${id}/verify`, {}),

  discover: (id: number): Promise<CapabilityReport> =>
    apiClient.post<CapabilityReport>(`/api/v1/connection/${id}/discover`, {}),
};