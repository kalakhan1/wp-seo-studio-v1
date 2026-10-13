/**
 * Thin fetch wrapper.
 *
 * Responsibilities:
 *   - Base URL from env (Vite dev proxy handles /api by default)
 *   - Attach JSON headers
 *   - Parse error envelopes into ApiError
 *   - Throw NetworkError on transport failure
 *   - Never send credentials in query strings or logs
 */

import { ApiError, NetworkError, type ApiErrorEnvelope } from "@/types/errors";

const DEFAULT_BASE_URL = "";

function getBaseUrl(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL;
  if (typeof fromEnv === "string" && fromEnv.length > 0) {
    return fromEnv.replace(/\/$/, "");
  }
  return DEFAULT_BASE_URL;
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  signal?: AbortSignal;
  headers?: Record<string, string>;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, signal, headers = {} } = options;
  const url = `${getBaseUrl()}${path}`;

  let response: Response;
  try {
    response = await fetch(url, {
      method,
      signal,
      headers: {
        Accept: "application/json",
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw err;
    }
    throw new NetworkError(
      err instanceof Error ? err.message : "Network request failed",
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");

  if (!response.ok) {
    let parsed: ApiErrorEnvelope | null = null;
    if (isJson) {
      try {
        parsed = (await response.json()) as ApiErrorEnvelope;
      } catch {
        parsed = null;
      }
    }
    if (parsed && parsed.error) {
      throw new ApiError({
        code: parsed.error.code,
        message: parsed.error.message,
        details: parsed.error.details ?? {},
        status: response.status,
        requestId: parsed.request_id ?? null,
      });
    }
    throw new ApiError({
      code: `HTTP_${response.status}`,
      message: response.statusText || "Request failed",
      status: response.status,
    });
  }

  if (isJson) {
    return (await response.json()) as T;
  }
  return (await response.text()) as unknown as T;
}

export const apiClient = {
  get: <T>(path: string, signal?: AbortSignal) =>
    request<T>(path, { method: "GET", signal }),
  post: <T>(path: string, body: unknown, signal?: AbortSignal) =>
    request<T>(path, { method: "POST", body, signal }),
  put: <T>(path: string, body: unknown, signal?: AbortSignal) =>
    request<T>(path, { method: "PUT", body, signal }),
  patch: <T>(path: string, body: unknown, signal?: AbortSignal) =>
    request<T>(path, { method: "PATCH", body, signal }),
  delete: <T>(path: string, signal?: AbortSignal) =>
    request<T>(path, { method: "DELETE", signal }),
};