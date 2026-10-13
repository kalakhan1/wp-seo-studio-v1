/**
 * Loads and updates non-secret application settings.
 *
 * Returns the latest snapshot, loading/error state, and an update function.
 */

import { useCallback, useEffect, useState } from "react";

import { apiClient } from "@/services/apiClient";
import { useAppStore } from "@/store/appStore";
import type { AppSettings, AppSettingsUpdate } from "@/types/api";
import { ApiError, NetworkError } from "@/types/errors";

export interface UseAppSettingsResult {
  settings: AppSettings | null;
  loading: boolean;
  error: string | null;
  update: (payload: AppSettingsUpdate) => Promise<AppSettings>;
  refresh: () => Promise<void>;
}

export function useAppSettings(): UseAppSettingsResult {
  const settings = useAppStore((s) => s.settings);
  const setSettings = useAppStore((s) => s.setSettings);

  const [loading, setLoading] = useState<boolean>(settings === null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<AppSettings>("/api/v1/app-settings");
      setSettings(data);
    } catch (err) {
      const message =
        err instanceof ApiError || err instanceof NetworkError
          ? err.message
          : "Failed to load settings";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [setSettings]);

  useEffect(() => {
    void load();
  }, [load]);

  const update = useCallback(
    async (payload: AppSettingsUpdate) => {
      const data = await apiClient.put<AppSettings>(
        "/api/v1/app-settings",
        payload,
      );
      setSettings(data);
      return data;
    },
    [setSettings],
  );

  const refresh = useCallback(async () => {
    await load();
  }, [load]);

  return { settings, loading, error, update, refresh };
}