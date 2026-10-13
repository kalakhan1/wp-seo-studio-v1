/**
 * Types mirroring backend/app/schemas/media.py
 */

export interface MediaItem {
  id: number;
  wp_media_id: number | null;
  filename: string;
  url: string | null;
  mime: string | null;
  size_bytes: number | null;
  width: number | null;
  height: number | null;
  alt_text: string | null;
  title: string | null;
  caption: string | null;
  description: string | null;
  content_hash: string | null;
  created_at: string;
  updated_at: string;
}

export interface MediaList {
  items: MediaItem[];
  total: number;
}

export interface MediaUpdateRequest {
  title?: string;
  alt_text?: string;
  caption?: string;
  description?: string;
  sync_to_wordpress?: boolean;
}

export interface MediaUploadResponse {
  media: MediaItem;
  wordpress_id: number;
  wordpress_url: string;
}