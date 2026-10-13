/**
 * API types mirroring the backend Pydantic schemas.
 *
 * Keep in sync with:
 *   backend/app/schemas/health.py
 *   backend/app/schemas/app_settings.py
 */

export interface ComponentHealth {
  name: string;
  status: "ok" | "degraded" | "failed";
  detail: string;
}

export interface HealthResponse {
  status: "ok" | "degraded" | "failed";
  mode: "mock" | "real";
  version: string;
  timestamp: string;
  components: ComponentHealth[];
}

export interface AppSettings {
  app_env: string;
  app_mode: "mock" | "real";
  log_level: "debug" | "info" | "warning" | "error" | "critical";
  log_format: "human" | "json";
  ai_provider: string;
  image_search_provider: string;
  http_timeout: number;
  http_max_retries: number;
}

export interface AppSettingsUpdate {
  log_level?: AppSettings["log_level"];
}

export interface RootResponse {
  name: string;
  version: string;
  docs: string;
  health: string;
}