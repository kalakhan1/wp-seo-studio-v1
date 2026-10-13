/**
 * Types mirroring backend/app/schemas/connection.py
 */

import type { SiteInfo, WPUser } from "@/types/capability";

export interface ConnectionTestRequest {
  base_url: string;
  username: string;
  wp_app_password: string;
  auth_method?: string;
  require_https?: boolean;
  wc_consumer_key?: string;
  wc_consumer_secret?: string;
}

export interface ConnectionTestResponse {
  ok: boolean;
  site_info: SiteInfo | null;
  current_user: WPUser | null;
  wc_available: boolean;
  message: string;
  warnings: string[];
}

export interface ConnectionSaveRequest {
  label: string;
  base_url: string;
  username: string;
  wp_app_password: string;
  auth_method?: string;
  require_https?: boolean;
  wc_consumer_key?: string;
  wc_consumer_secret?: string;
  notes?: string | null;
}

export interface Connection {
  id: number;
  label: string;
  base_url: string;
  username: string;
  auth_method: string;
  require_https: boolean;
  notes: string | null;
  has_wc_credentials: boolean;
  last_verified_at: string | null;
  last_verified_ok: boolean;
  created_at: string;
  updated_at: string;
}

export interface ConnectionList {
  connections: Connection[];
}