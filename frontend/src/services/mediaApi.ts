/**
 * Media API client. Handles multipart uploads and JSON operations.
 */

import { ApiError, NetworkError } from "@/types/errors";
import type {
  MediaItem,
  MediaList,
  MediaUpdateRequest,
  MediaUploadResponse,
} from "@/types/media";

const BASE_URL = "";

function buildUrl(path: string): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL;
  const base = typeof fromEnv === "string" && fromEnv.length > 0
    ? fromEnv.replace(/\/$/, "")
    : BASE_URL;
  return `${base}${path}`;
}

async function parseErrorEnvelope(
  response: Response,
): Promise<ApiError> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    try {
      const body = await response.json();
      if (body?.error) {
        return new ApiError({
          code: body.error.code,
          message: body.error.message,
          details: body.error.details ?? {},
          status: response.status,
          requestId: body.request_id ?? null,
        });
      }
    } catch {
      // fall through
    }
  }
  return new ApiError({
    code: `HTTP_${response.status}`,
    message: response.statusText || "Request failed",
    status: response.status,
  });
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(buildUrl(path), {
      method: "GET",
      signal,
      headers: { Accept: "application/json" },
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new NetworkError(
      err instanceof Error ? err.message : "Network request failed",
    );
  }
  if (!response.ok) throw await parseErrorEnvelope(response);
  return (await response.json()) as T;
}

async function sendJson<T>(
  method: "PATCH" | "POST",
  path: string,
  body: unknown,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(buildUrl(path), {
      method,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
  } catch (err) {
    throw new NetworkError(
      err instanceof Error ? err.message : "Network request failed",
    );
  }
  if (!response.ok) throw await parseErrorEnvelope(response);
  return (await response.json()) as T;
}

async function deleteVoid(path: string): Promise<void> {
  let response: Response;
  try {
    response = await fetch(buildUrl(path), {
      method: "DELETE",
      headers: { Accept: "application/json" },
    });
  } catch (err) {
    throw new NetworkError(
      err instanceof Error ? err.message : "Network request failed",
    );
  }
  if (!response.ok && response.status !== 204) {
    throw await parseErrorEnvelope(response);
  }
}

export interface UploadMediaArgs {
  connectionId: number;
  file: File;
  title?: string;
  altText?: string;
  caption?: string;
  description?: string;
  onProgress?: (percent: number) => void;
}

export const mediaApi = {
  list: (params: {
    connectionId?: number;
    query?: string;
    limit?: number;
    offset?: number;
    signal?: AbortSignal;
  } = {}): Promise<MediaList> => {
    const search = new URLSearchParams();
    if (params.connectionId !== undefined) {
      search.set("connection_id", String(params.connectionId));
    }
    if (params.query) search.set("q", params.query);
    if (params.limit !== undefined) search.set("limit", String(params.limit));
    if (params.offset !== undefined) search.set("offset", String(params.offset));
    const qs = search.toString();
    return getJson<MediaList>(`/api/v1/media${qs ? `?${qs}` : ""}`, params.signal);
  },

  get: (id: number): Promise<MediaItem> =>
    getJson<MediaItem>(`/api/v1/media/${id}`),

  update: (id: number, payload: MediaUpdateRequest): Promise<MediaItem> =>
    sendJson<MediaItem>("PATCH", `/api/v1/media/${id}`, payload),

  remove: (id: number, force = false): Promise<void> =>
    deleteVoid(`/api/v1/media/${id}${force ? "?force=true" : ""}`),

  upload: (args: UploadMediaArgs): Promise<MediaUploadResponse> => {
    return new Promise((resolve, reject) => {
      const form = new FormData();
      form.append("connection_id", String(args.connectionId));
      form.append("file", args.file);
      if (args.title !== undefined) form.append("title", args.title);
      if (args.altText !== undefined) form.append("alt_text", args.altText);
      if (args.caption !== undefined) form.append("caption", args.caption);
      if (args.description !== undefined) {
        form.append("description", args.description);
      }

      const xhr = new XMLHttpRequest();
      xhr.open("POST", buildUrl("/api/v1/media/upload"));
      xhr.responseType = "json";

      if (args.onProgress) {
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            args.onProgress?.(Math.round((e.loaded / e.total) * 100));
          }
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(xhr.response as MediaUploadResponse);
          return;
        }
        const body = xhr.response as
          | { error?: { code: string; message: string; details?: Record<string, unknown> } }
          | null;
        if (body && body.error) {
          reject(
            new ApiError({
              code: body.error.code,
              message: body.error.message,
              details: body.error.details ?? {},
              status: xhr.status,
            }),
          );
        } else {
          reject(
            new ApiError({
              code: `HTTP_${xhr.status}`,
              message: xhr.statusText || "Upload failed",
              status: xhr.status,
            }),
          );
        }
      };

      xhr.onerror = () => {
        reject(new NetworkError("Upload failed due to a network error"));
      };

      xhr.send(form);
    });
  },
};