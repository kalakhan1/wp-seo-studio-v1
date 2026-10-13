/**
 * Polls /api/v1/health every 30 seconds and stores the result in the app store.
 *
 * Safe to mount once at the layout level.
 */

import { useEffect } from "react";

import { apiClient } from "@/services/apiClient";
import { useAppStore } from "@/store/appStore";
import type { HealthResponse } from "@/types/api";

const POLL_INTERVAL_MS = 30_000;

export interface UseHealthResult {
  health: HealthResponse | null;
}

export function useHealth(): UseHealthResult {
  const health = useAppStore((s) => s.health);
  const setHealth = useAppStore((s) => s.setHealth);

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;

    const fetchHealth = async () => {
      try {
        const data = await apiClient.get<HealthResponse>(
          "/api/v1/health",
          controller.signal,
        );
        if (!cancelled) setHealth(data);
      } catch (err) {
        if (cancelled) return;
        if (err instanceof DOMException && err.name === "AbortError") return;
        // On error we keep the last known health; a null would hide the issue.
        // eslint-disable-next-line no-console
        console.warn("Health check failed:", err);
      }
    };

    void fetchHealth();
    const interval = window.setInterval(fetchHealth, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      controller.abort();
      window.clearInterval(interval);
    };
  }, [setHealth]);

  return { health };
}