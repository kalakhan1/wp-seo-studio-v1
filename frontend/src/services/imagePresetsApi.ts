/**
 * Image presets API wrappers.
 */

import { apiClient } from "@/services/apiClient";
import type {
  DiscoveredSizesResponse,
  PresetsResponse,
} from "@/types/imagePresets";

export const imagePresetsApi = {
  listPresets: (): Promise<PresetsResponse> =>
    apiClient.get<PresetsResponse>("/api/v1/image-presets"),

  discoverSizes: (
    connectionId: number,
    mediaId?: number,
  ): Promise<DiscoveredSizesResponse> => {
    const params = new URLSearchParams({
      connection_id: String(connectionId),
    });
    if (mediaId !== undefined) params.set("media_id", String(mediaId));
    return apiClient.get<DiscoveredSizesResponse>(
      `/api/v1/image-presets/discovered?${params.toString()}`,
    );
  },
};