/**
 * Global app state (Zustand).
 *
 * Phase 1 scope:
 *   - last known health report
 *   - last known app settings
 *   - mode indicator for TopNav
 *
 * Data fetching happens in hooks (useHealth, useAppSettings); the store
 * only holds the latest snapshot so multiple components can read it.
 */

import { create } from "zustand";

import type { AppSettings, HealthResponse } from "@/types/api";

interface AppState {
  health: HealthResponse | null;
  settings: AppSettings | null;
  setHealth: (health: HealthResponse | null) => void;
  setSettings: (settings: AppSettings | null) => void;
  reset: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  health: null,
  settings: null,
  setHealth: (health) => set({ health }),
  setSettings: (settings) => set({ settings }),
  reset: () => set({ health: null, settings: null }),
}));