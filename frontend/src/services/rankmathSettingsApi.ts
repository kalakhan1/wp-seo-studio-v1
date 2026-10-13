/**
 * Rank Math global settings API wrappers.
 */

import { apiClient } from "@/services/apiClient";
import type {
  RankMathCapabilityStatus,
  RankMathSettingsResponse,
  RankMathSettingUpdate,
  RankMathSettingsUpdateResponse,
} from "@/types/rankmathSettings";

export const rankmathSettingsApi = {
  getStatus: (connectionId: number): Promise<RankMathCapabilityStatus> =>
    apiClient.get<RankMathCapabilityStatus>(
      `/api/v1/rankmath/settings/status?connection_id=${connectionId}`,
    ),

  getSettings: (connectionId: number): Promise<RankMathSettingsResponse> =>
    apiClient.get<RankMathSettingsResponse>(
      `/api/v1/rankmath/settings?connection_id=${connectionId}`,
    ),

  updateSettings: (
    connectionId: number,
    payload: RankMathSettingUpdate,
  ): Promise<RankMathSettingsUpdateResponse> =>
    apiClient.put<RankMathSettingsUpdateResponse>(
      `/api/v1/rankmath/settings?connection_id=${connectionId}`,
      payload,
    ),
};