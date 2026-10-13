/**
 * WooCommerce settings API wrappers.
 */

import { apiClient } from "@/services/apiClient";
import type {
  StoreProfileResponse,
  WCSetting,
  WCSettingValue,
  WCSettingsGroupResponse,
} from "@/types/wcSettings";

export const wcSettingsApi = {
  listGroups: (): Promise<string[]> =>
    apiClient.get<string[]>("/api/v1/wc/settings/groups"),

  getStoreProfile: (connectionId: number): Promise<StoreProfileResponse> =>
    apiClient.get<StoreProfileResponse>(
      `/api/v1/wc/settings/store-profile?connection_id=${connectionId}`,
    ),

  getGroup: (
    connectionId: number,
    group: string,
  ): Promise<WCSettingsGroupResponse> =>
    apiClient.get<WCSettingsGroupResponse>(
      `/api/v1/wc/settings/${group}?connection_id=${connectionId}`,
    ),

  getSetting: (
    connectionId: number,
    group: string,
    settingId: string,
  ): Promise<WCSetting> =>
    apiClient.get<WCSetting>(
      `/api/v1/wc/settings/${group}/${settingId}?connection_id=${connectionId}`,
    ),

  updateSetting: (
    connectionId: number,
    group: string,
    settingId: string,
    value: WCSettingValue,
  ): Promise<WCSetting> =>
    apiClient.put<WCSetting>(
      `/api/v1/wc/settings/${group}/${settingId}?connection_id=${connectionId}`,
      { value },
    ),
};