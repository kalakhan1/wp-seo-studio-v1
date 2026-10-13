/**
 * Types mirroring backend/app/schemas/rankmath_settings.py
 */

export interface RankMathSettings {
  title_separator: string;
  homepage_title: string;
  homepage_description: string;
  sitemap_enabled: boolean;
  sitemap_include_products: boolean;
  sitemap_include_posts: boolean;
  sitemap_include_pages: boolean;
  noindex_empty_category: boolean;
  noindex_search: boolean;
  noindex_author_archives: boolean;
  noindex_date_archives: boolean;
  breadcrumbs_enabled: boolean;
  wc_remove_category_base: boolean;
  wc_show_product_breadcrumbs: boolean;
}

export type RankMathSettingUpdate = Partial<RankMathSettings>;

export interface RankMathSettingsResponse {
  settings: RankMathSettings;
  discovered_at: string;
  rank_math_version: string;
  source: "companion" | "unavailable";
  reason: string;
  warnings: string[];
}

export interface RankMathSettingsUpdateResponse {
  settings: RankMathSettings;
  changed: string[];
  warnings: string[];
}

export interface RankMathCapabilityStatus {
  plugin_available: boolean;
  rank_math_active: boolean;
  version: string;
  readable_keys: string[];
  reason: string;
  evidence: Record<string, unknown>;
}