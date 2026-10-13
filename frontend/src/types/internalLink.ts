/**
 * Types mirroring backend/app/schemas/internal_link.py
 */

export type LinkType =
  | "contextual"
  | "related_product"
  | "related_article"
  | "category"
  | "brand"
  | "footer_related";

export interface SearchResultItem {
  id: number;
  type: string;
  title: string;
  url: string;
  slug: string;
  excerpt: string;
}

export interface SearchResponse {
  items: SearchResultItem[];
  warnings: string[];
}

export interface SuggestedLink {
  target_id: number;
  target_type: string;
  title: string;
  url: string;
  score: number;
  reason: string;
  suggested_anchor: string;
}

export interface SuggestResponse {
  items: SuggestedLink[];
  warnings: string[];
}

export interface ValidateUrlRequest {
  url: string;
}

export interface ValidateUrlResponse {
  ok: boolean;
  reason: string;
  normalized_url: string;
  host: string;
}

export interface AnchorTextCheckRequest {
  anchor_text: string;
  existing_anchors: string[];
}

export interface AnchorTextCheckResponse {
  warnings: string[];
  exact_match_count: number;
}