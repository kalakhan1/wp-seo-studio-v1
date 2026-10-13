/**
 * Types mirroring backend/app/schemas/content.py
 */

export type ContentKind = "post" | "page";
export type ContentStatus =
  | "draft"
  | "publish"
  | "future"
  | "pending"
  | "private";

export interface RankMathMeta {
  title?: string | null;
  description?: string | null;
  focus_keyword?: string | null;
  canonical_url?: string | null;
  robots?: string[];
  facebook_title?: string | null;
  facebook_description?: string | null;
  facebook_image?: string | null;
  twitter_title?: string | null;
  twitter_description?: string | null;
  twitter_image?: string | null;
}

export interface ContentCreateRequest {
  connection_id: number;
  kind: ContentKind;
  title: string;
  slug?: string;
  content?: string;
  excerpt?: string;
  status?: ContentStatus;
  scheduled_date?: string | null;
  author_id?: number | null;
  featured_media_id?: number | null;
  categories?: number[];
  tags?: number[];
  parent_id?: number | null;
  menu_order?: number;
  comment_status?: "open" | "closed";
  ping_status?: "open" | "closed";
  rank_math?: RankMathMeta | null;
}

export interface ContentUpdateRequest {
  connection_id: number;
  title?: string;
  slug?: string;
  content?: string;
  excerpt?: string;
  status?: ContentStatus;
  scheduled_date?: string | null;
  featured_media_id?: number | null;
  categories?: number[];
  tags?: number[];
  parent_id?: number | null;
  menu_order?: number;
  comment_status?: "open" | "closed";
  ping_status?: "open" | "closed";
  rank_math?: RankMathMeta | null;
}

export interface ContentPublishResponse {
  success: boolean;
  partial: boolean;
  wp_object_id: number | null;
  wp_object_type: ContentKind;
  permalink: string | null;
  status: string | null;
  title: string;
  slug: string;
  rank_math_written: boolean;
  rank_math_error: string | null;
  message: string;
  warnings: string[];
}

export interface ContentGetResponse {
  id: number;
  kind: ContentKind;
  status: string;
  slug: string;
  permalink: string;
  title: string;
  content: string;
  excerpt: string;
  author_id: number;
  featured_media_id: number;
  parent_id: number;
  menu_order: number;
  comment_status: string;
  ping_status: string;
  categories: number[];
  tags: number[];
  date: string;
  modified: string;
  rank_math: RankMathMeta | null;
  rank_math_available: boolean;
  rank_math_reason: string | null;
}

export interface CategoryItem {
  id: number;
  name: string;
  slug: string;
  parent: number;
  count: number;
}

export interface TagItem {
  id: number;
  name: string;
  slug: string;
  count: number;
}

export interface CategoryListResponse {
  items: CategoryItem[];
}

export interface TagListResponse {
  items: TagItem[];
}