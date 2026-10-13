/**
 * Types mirroring backend/app/schemas/image_presets.py
 */

export type AspectRatio =
  | "1:1"
  | "4:5"
  | "3:4"
  | "4:3"
  | "3:2"
  | "16:9"
  | "2:3"
  | "custom";

export type ObjectFit = "cover" | "contain" | "fill" | "none" | "scale-down";

export type ObjectPosition = "center" | "top" | "bottom" | "left" | "right" | "custom";

export interface RegisteredImageSize {
  name: string;
  width: number;
  height: number;
  crop: boolean;
}

export interface SuggestedPreset {
  key: string;
  label: string;
  description: string;
  width: number;
  height: number;
  crop: boolean;
  aspect_ratio: AspectRatio;
}

export interface CSSPreset {
  key: string;
  label: string;
  description: string;
  aspect_ratio: AspectRatio;
  object_fit: ObjectFit;
  object_position: ObjectPosition;
  border_radius: string;
  background: string;
}

export interface DiscoveredSizesResponse {
  source_media_id: number;
  source_media_url: string;
  sizes: RegisteredImageSize[];
  warnings: string[];
}

export interface PresetsResponse {
  suggested: SuggestedPreset[];
  css: CSSPreset[];
}