/**
 * Error shapes returned by the backend.
 *
 * All API errors use this envelope:
 *   { error: { code, message, details }, request_id }
 */

export interface ApiErrorBody {
  code: string;
  message: string;
  details: Record<string, unknown>;
}

export interface ApiErrorEnvelope {
  error: ApiErrorBody;
  request_id?: string | null;
}

/**
 * Client-side error class used across the app.
 * Preserves the backend code so the UI can branch on specific errors.
 */
export class ApiError extends Error {
  readonly code: string;
  readonly details: Record<string, unknown>;
  readonly status: number;
  readonly requestId: string | null;

  constructor(params: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    status: number;
    requestId?: string | null;
  }) {
    super(params.message);
    this.name = "ApiError";
    this.code = params.code;
    this.details = params.details ?? {};
    this.status = params.status;
    this.requestId = params.requestId ?? null;
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NetworkError";
  }
}