/**
 * Content + taxonomy API wrappers.
 */

import { apiClient } from "@/services/apiClient";
import type {
  CategoryListResponse,
  ContentCreateRequest,
  ContentGetResponse,
  ContentKind,
  ContentPublishResponse,
  ContentUpdateRequest,
  TagListResponse,
} from "@/types/content";

export const contentApi = {
  createPost: (payload: ContentCreateRequest): Promise<ContentPublishResponse> =>
    apiClient.post<ContentPublishResponse>("/api/v1/content/post", {
      ...payload,
      kind: "post",
    }),

  createPage: (payload: ContentCreateRequest): Promise<ContentPublishResponse> =>
    apiClient.post<ContentPublishResponse>("/api/v1/content/page", {
      ...payload,
      kind: "page",
    }),

  get: (
    kind: ContentKind,
    id: number,
    connectionId: number,
  ): Promise<ContentGetResponse> =>
    apiClient.get<ContentGetResponse>(
      `/api/v1/content/${kind}/${id}?connection_id=${connectionId}`,
    ),

  update: (
    kind: ContentKind,
    id: number,
    payload: ContentUpdateRequest,
  ): Promise<ContentPublishResponse> =>
    apiClient.put<ContentPublishResponse>(
      `/api/v1/content/${kind}/${id}`,
      payload,
    ),
};

export const taxonomyApi = {
  listCategories: (
    connectionId: number,
    search?: string,
  ): Promise<CategoryListResponse> => {
    const params = new URLSearchParams({ connection_id: String(connectionId) });
    if (search) params.set("search", search);
    return apiClient.get<CategoryListResponse>(
      `/api/v1/taxonomies/categories?${params.toString()}`,
    );
  },

  listTags: (
    connectionId: number,
    search?: string,
  ): Promise<TagListResponse> => {
    const params = new URLSearchParams({ connection_id: String(connectionId) });
    if (search) params.set("search", search);
    return apiClient.get<TagListResponse>(
      `/api/v1/taxonomies/tags?${params.toString()}`,
    );
  },
};