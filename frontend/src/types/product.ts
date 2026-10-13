/**
 * Types mirroring backend/app/schemas/product.py
 */

import type { RankMathMeta } from "@/types/content";

export type ProductStatus = "draft" | "pending" | "private" | "publish";
export type ProductType = "simple";
export type CatalogVisibility = "visible" | "catalog" | "search" | "hidden";
export type StockStatus = "instock" | "outofstock" | "onbackorder";
export type Backorders = "no" | "notify" | "yes";
export type TaxStatus = "taxable" | "shipping" | "none";

export interface ProductImageInput {
  id?: number | null;
  src?: string | null;
  alt?: string | null;
}

export interface ProductDimensions {
  length: string;
  width: string;
  height: string;
}

export interface ProductCreateRequest {
  connection_id: number;
  name: string;
  slug?: string;
  type?: ProductType;
  status?: ProductStatus;
  featured?: boolean;
  catalog_visibility?: CatalogVisibility;
  description?: string;
  short_description?: string;
  sku?: string;
  regular_price?: string;
  sale_price?: string;
  date_on_sale_from?: string | null;
  date_on_sale_to?: string | null;
  tax_status?: TaxStatus;
  tax_class?: string;
  manage_stock?: boolean;
  stock_quantity?: number | null;
  stock_status?: StockStatus;
  backorders?: Backorders;
  low_stock_amount?: number | null;
  sold_individually?: boolean;
  weight?: string;
  dimensions?: ProductDimensions;
  shipping_class?: string;
  category_ids?: number[];
  tag_ids?: number[];
  images?: ProductImageInput[];
  upsell_ids?: number[];
  cross_sell_ids?: number[];
  reviews_allowed?: boolean;
  purchase_note?: string;
  menu_order?: number;
  rank_math?: RankMathMeta | null;
}

export interface ProductUpdateRequest {
  connection_id: number;
  name?: string;
  slug?: string;
  status?: ProductStatus;
  featured?: boolean;
  catalog_visibility?: CatalogVisibility;
  description?: string;
  short_description?: string;
  sku?: string;
  regular_price?: string;
  sale_price?: string;
  date_on_sale_from?: string | null;
  date_on_sale_to?: string | null;
  tax_status?: TaxStatus;
  tax_class?: string;
  manage_stock?: boolean;
  stock_quantity?: number | null;
  stock_status?: StockStatus;
  backorders?: Backorders;
  low_stock_amount?: number | null;
  sold_individually?: boolean;
  weight?: string;
  dimensions?: ProductDimensions;
  shipping_class?: string;
  category_ids?: number[];
  tag_ids?: number[];
  images?: ProductImageInput[];
  upsell_ids?: number[];
  cross_sell_ids?: number[];
  reviews_allowed?: boolean;
  purchase_note?: string;
  menu_order?: number;
  rank_math?: RankMathMeta | null;
}

export interface ProductResponse {
  id: number;
  name: string;
  slug: string;
  type: string;
  status: string;
  permalink: string;
  sku: string;
  price: string;
  regular_price: string;
  sale_price: string;
  description: string;
  short_description: string;
  featured: boolean;
  catalog_visibility: string;
  manage_stock: boolean;
  stock_quantity: number | null;
  stock_status: string;
  weight: string;
  dimensions: Record<string, string>;
  category_ids: number[];
  tag_ids: number[];
  image_ids: number[];
  image_urls: string[];
  menu_order: number;
  parent_id: number;
  rank_math_available: boolean;
  rank_math: RankMathMeta | null;
  rank_math_reason: string | null;
}

export interface ProductPublishResponse {
  success: boolean;
  partial: boolean;
  wp_object_id: number | null;
  wp_object_type: "product";
  permalink: string | null;
  status: string | null;
  name: string;
  slug: string;
  sku: string;
  rank_math_written: boolean;
  rank_math_error: string | null;
  message: string;
  warnings: string[];
}

export interface WCCategoryItem {
  id: number;
  name: string;
  slug: string;
  parent: number;
  count: number;
}

export interface WCTagItem {
  id: number;
  name: string;
  slug: string;
  count: number;
}

export interface WCCategoryListResponse {
  items: WCCategoryItem[];
}

export interface WCTagListResponse {
  items: WCTagItem[];
}