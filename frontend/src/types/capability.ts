/**
 * Types mirroring backend/app/schemas/capability.py and
 * backend/app/integrations/wordpress/types.py
 */

export interface SiteInfo {
  name: string;
  description: string;
  url: string;
  home: string;
  gmt_offset: number;
  timezone_string: string;
  namespaces: string[];
}

export interface WPUser {
  id: number;
  name: string;
  slug: string;
  roles: string[];
  capabilities: Record<string, boolean>;
}

export interface PostType {
  slug: string;
  name: string;
  rest_base: string;
  rest_namespace: string;
  hierarchical: boolean;
  supports: string[];
}

export interface Taxonomy {
  slug: string;
  name: string;
  rest_base: string;
  rest_namespace: string;
  hierarchical: boolean;
  types: string[];
}

export type CapabilityStatus =
  | "supported"
  | "read_only"
  | "requires_elevated"
  | "requires_plugin"
  | "requires_manual_setup"
  | "not_verified"
  | "unsupported";

export interface CapabilityItem {
  key: string;
  label: string;
  category: string;
  status: CapabilityStatus;
  method: string;
  endpoint: string;
  reason: string;
  evidence: Record<string, unknown>;
}

export interface CapabilitySummary {
  supported: number;
  read_only: number;
  requires_elevated: number;
  requires_plugin: number;
  requires_manual_setup: number;
  not_verified: number;
  unsupported: number;
}

export interface RankMathSummary {
  plugin_detected: boolean;
  companion_plugin_detected: boolean;
  companion_settings_available: boolean;
  namespaces_found: string[];
  reason: string;
  evidence: Record<string, unknown>;
}

export interface CapabilityReport {
  base_url: string;
  discovered_at: string;
  site_info: SiteInfo | null;
  current_user: WPUser | null;
  post_types: PostType[];
  taxonomies: Taxonomy[];
  capabilities: CapabilityItem[];
  summary: CapabilitySummary;
  rankmath: RankMathSummary;
  warnings: string[];
}