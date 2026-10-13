/**
 * Payment gateway + COD API wrappers.
 */

import { apiClient } from "@/services/apiClient";
import type {
  CODSettings,
  CODStatus,
  WCGateway,
  WCGatewayListResponse,
} from "@/types/wcGateway";

export const wcGatewayApi = {
  list: (connectionId: number): Promise<WCGatewayListResponse> =>
    apiClient.get<WCGatewayListResponse>(
      `/api/v1/wc/gateways?connection_id=${connectionId}`,
    ),

  getCOD: (connectionId: number): Promise<CODStatus> =>
    apiClient.get<CODStatus>(
      `/api/v1/wc/gateways/cod?connection_id=${connectionId}`,
    ),

  updateCOD: (connectionId: number, payload: CODSettings): Promise<WCGateway> =>
    apiClient.put<WCGateway>(
      `/api/v1/wc/gateways/cod?connection_id=${connectionId}`,
      payload,
    ),

  get: (connectionId: number, gatewayId: string): Promise<WCGateway> =>
    apiClient.get<WCGateway>(
      `/api/v1/wc/gateways/${gatewayId}?connection_id=${connectionId}`,
    ),
};