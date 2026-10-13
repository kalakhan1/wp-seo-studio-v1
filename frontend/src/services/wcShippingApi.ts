/**
 * Shipping zones + methods API wrappers.
 */

import { apiClient } from "@/services/apiClient";
import type {
  AvailableMethodsResponse,
  MethodAddRequest,
  MethodUpdateRequest,
  WCShippingMethod,
  WCShippingZoneDetail,
  ZoneCreateRequest,
  ZoneListResponse,
  ZoneLocation,
  ZoneUpdateRequest,
} from "@/types/wcShipping";

export const wcShippingApi = {
  listZones: (connectionId: number): Promise<ZoneListResponse> =>
    apiClient.get<ZoneListResponse>(
      `/api/v1/wc/shipping/zones?connection_id=${connectionId}`,
    ),

  getZone: (connectionId: number, zoneId: number): Promise<WCShippingZoneDetail> =>
    apiClient.get<WCShippingZoneDetail>(
      `/api/v1/wc/shipping/zones/${zoneId}?connection_id=${connectionId}`,
    ),

  createZone: (
    connectionId: number,
    payload: ZoneCreateRequest,
  ): Promise<WCShippingZoneDetail> =>
    apiClient.post<WCShippingZoneDetail>(
      `/api/v1/wc/shipping/zones?connection_id=${connectionId}`,
      payload,
    ),

  updateZone: (
    connectionId: number,
    zoneId: number,
    payload: ZoneUpdateRequest,
  ): Promise<WCShippingZoneDetail> =>
    apiClient.put<WCShippingZoneDetail>(
      `/api/v1/wc/shipping/zones/${zoneId}?connection_id=${connectionId}`,
      payload,
    ),

  deleteZone: (connectionId: number, zoneId: number): Promise<void> =>
    apiClient.delete<void>(
      `/api/v1/wc/shipping/zones/${zoneId}?connection_id=${connectionId}`,
    ),

  updateLocations: (
    connectionId: number,
    zoneId: number,
    locations: ZoneLocation[],
  ): Promise<WCShippingZoneDetail> =>
    apiClient.put<WCShippingZoneDetail>(
      `/api/v1/wc/shipping/zones/${zoneId}/locations?connection_id=${connectionId}`,
      { locations },
    ),

  addMethod: (
    connectionId: number,
    zoneId: number,
    payload: MethodAddRequest,
  ): Promise<WCShippingMethod> =>
    apiClient.post<WCShippingMethod>(
      `/api/v1/wc/shipping/zones/${zoneId}/methods?connection_id=${connectionId}`,
      payload,
    ),

  updateMethod: (
    connectionId: number,
    zoneId: number,
    instanceId: number,
    payload: MethodUpdateRequest,
  ): Promise<WCShippingMethod> =>
    apiClient.put<WCShippingMethod>(
      `/api/v1/wc/shipping/zones/${zoneId}/methods/${instanceId}?connection_id=${connectionId}`,
      payload,
    ),

  deleteMethod: (
    connectionId: number,
    zoneId: number,
    instanceId: number,
  ): Promise<void> =>
    apiClient.delete<void>(
      `/api/v1/wc/shipping/zones/${zoneId}/methods/${instanceId}?connection_id=${connectionId}`,
    ),

  listAvailableMethods: (
    connectionId: number,
  ): Promise<AvailableMethodsResponse> =>
    apiClient.get<AvailableMethodsResponse>(
      `/api/v1/wc/shipping/methods?connection_id=${connectionId}`,
    ),
};