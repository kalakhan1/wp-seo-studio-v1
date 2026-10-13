/**
 * Internal linking API wrappers.
 */

import { apiClient } from "@/services/apiClient";
import type {
  AnchorTextCheckResponse,
  SearchResponse,
  SuggestResponse,
  ValidateUrlResponse,
} from "@/types/internalLink";

export const internalLinkApi = {
  search: (
    connectionId: number,
    query: string,
    opts: {
      posts?: boolean;
      pages?: boolean;
      products?: boolean;
      perPage?: number;
    } = {},
  ): Promise<SearchResponse> => {
    const params = new URLSearchParams({
      connection_id: String(connectionId),
      q: query,
      posts: String(opts.posts ?? true),
      pages: String(opts.pages ?? true),
      products: String(opts.products ?? true),
    });
    if (opts.perPage) params.set("per_page", String(opts.perPage));
    return apiClient.get<SearchResponse>(
      `/api/v1/internal-links/search?${params.toString()}`,
    );
  },

  suggest: (
    connectionId: number,
    sourceTitle: string,
    opts: {
      sourceContent?: string;
      excludeIds?: number[];
      limit?: number;
    } = {},
  ): Promise<SuggestResponse> => {
    const params = new URLSearchParams({
      connection_id: String(connectionId),
      source_title: sourceTitle,
    });
    if (opts.sourceContent) params.set("source_content", opts.sourceContent);
    if (opts.excludeIds?.length) {
      params.set("exclude_ids", opts.excludeIds.join(","));
    }
    if (opts.limit) params.set("limit", String(opts.limit));
    return apiClient.post<SuggestResponse>(
      `/api/v1/internal-links/suggest?${params.toString()}`,
      {},
    );
  },

  validateUrl: (
    connectionId: number,
    url: string,
  ): Promise<ValidateUrlResponse> =>
    apiClient.post<ValidateUrlResponse>(
      `/api/v1/internal-links/validate-url?connection_id=${connectionId}`,
      { url },
    ),

  checkAnchor: (
    anchorText: string,
    existingAnchors: string[],
  ): Promise<AnchorTextCheckResponse> =>
    apiClient.post<AnchorTextCheckResponse>(
      "/api/v1/internal-links/check-anchor",
      { anchor_text: anchorText, existing_anchors: existingAnchors },
    ),
};