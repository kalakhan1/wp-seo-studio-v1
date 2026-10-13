/**
 * Types mirroring backend/app/schemas/queue.py
 */

export interface QueueJob {
  id: number;
  job_id: string;
  job_type: string;
  status: string;
  progress: number;
  attempts: number;
  max_attempts: number;
  error: string | null;
  payload: Record<string, unknown> | null;
  result: Record<string, unknown> | null;
  scheduled_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  connection_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface QueueListResponse {
  items: QueueJob[];
  total: number;
}

export interface QueueSummary {
  pending: number;
  running: number;
  success: number;
  failed: number;
  partial: number;
  cancelled: number;
  retrying: number;
}