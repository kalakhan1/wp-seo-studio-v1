/**
 * Product + product taxonomy API wrappers.
 */

import { apiClient } from "@/services/apiClient";
import type {
  ProductCreateRequest,
  ProductPublishResponse,
  ProductResponse,
  ProductUpdateRequest,
  WCCategoryListResponse,
  WCTagListResponse,
} from "@/types/product";

export const productApi = {
  create: (payload: ProductCreateRequest): Promise<ProductPublishResponse> =>
    apiClient.post<ProductPublishResponse>("/api/v1/products", payload),

  list: (
    connectionId: number,
    opts: {
      search?: string;
      status?: string;
      perPage?: number;
      page?: number;
    } = {},
  ): Promise<ProductResponse[]> => {
    const params = new URLSearchParams({
      connection_id: String(connectionId),
    });
    if (opts.search) params.set("search", opts.search);
    if (opts.status) params.set("status", opts.status);
    if (opts.perPage) params.set("per_page", String(opts.perPage));
    if (opts.page) params.set("page", String(opts.page));
    return apiClient.get<ProductResponse[]>(`/api/v1/products?${params.toString()}`);
  },

  get: (productId: number, connectionId: number): Promise<ProductResponse> =>
    apiClient.get<ProductResponse>(
      `/api/v1/products/${productId}?connection_id=${connectionId}`,
    ),

  update: (
    productId: number,
    payload: ProductUpdateRequest,
  ): Promise<ProductPublishResponse> =>
    apiClient.put<ProductPublishResponse>(
      `/api/v1/products/${productId}`,
      payload,
    ),

  remove: (productId: number, connectionId: number, force = false): Promise<void> =>
    apiClient.delete<void>(
      `/api/v1/products/${productId}?connection_id=${connectionId}${force ? "&force=true" : ""}`,
    ),
};

export const productTaxonomyApi = {
  listCategories: (
    connectionId: number,
    search?: string,
  ): Promise<WCCategoryListResponse> => {
    const params = new URLSearchParams({ connection_id: String(connectionId) });
    if (search) params.set("search", search);
    return apiClient.get<WCCategoryListResponse>(
      `/api/v1/products/taxonomies/categories?${params.toString()}`,
    );
  },

  listTags: (
    connectionId: number,
    search?: string,
  ): Promise<WCTagListResponse> => {
    const params = new URLSearchParams({ connection_id: String(connectionId) });
    if (search) params.set("search", search);
    return apiClient.get<WCTagListResponse>(
      `/api/v1/products/taxonomies/tags?${params.toString()}`,
    );
  },
};