/**
 * Types mirroring backend/app/schemas/history.py
 */

export interface HistoryEntry {
  id: number;
  object_type: string;
  operation: string;
  status: string;
  wp_object_id: number | null;
  permalink: string | null;
  message: string | null;
  idempotency_key: string | null;
  connection_id: number | null;
  created_at: string;
}

export interface HistoryListResponse {
  items: HistoryEntry[];
  total: number;
}

export interface HistorySummary {
  total: number;
  success: number;
  failed: number;
  partial: number;
}