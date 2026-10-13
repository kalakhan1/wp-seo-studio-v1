/**
 * Types mirroring backend/app/schemas/backup.py
 */

export interface BackupBundle {
  format: "wp-seo-studio.backup.v1";
  created_at: string;
  app_version: string;
  connections: Array<Record<string, unknown>>;
  prompt_templates: Array<Record<string, unknown>>;
  app_settings: Array<Record<string, unknown>>;
  notes: string;
}

export interface BackupExportResponse {
  bundle: BackupBundle;
  warnings: string[];
}

export interface BackupImportRequest {
  bundle: BackupBundle;
  dry_run: boolean;
  include_connections: boolean;
  include_prompt_templates: boolean;
  include_app_settings: boolean;
}

export interface BackupImportReport {
  dry_run: boolean;
  connections_created: number;
  connections_skipped: number;
  prompt_templates_updated: number;
  app_settings_updated: number;
  warnings: string[];
  errors: string[];
}