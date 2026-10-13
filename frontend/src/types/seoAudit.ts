/**
 * Types mirroring backend/app/schemas/seo_audit.py
 */

export type Severity = "info" | "pass" | "warn" | "fail";

export type CheckCategory =
  | "connection"
  | "permalinks"
  | "sitemap"
  | "robots"
  | "indexability"
  | "content"
  | "media"
  | "structure"
  | "performance";

export interface AuditFinding {
  check_id: string;
  label: string;
  category: CheckCategory;
  severity: Severity;
  message: string;
  evidence: Record<string, unknown>;
  suggested_fix: string;
  affected_urls: string[];
  action_path: string;
}

export interface AuditSummary {
  pass_count: number;
  warn_count: number;
  fail_count: number;
  info_count: number;
  total: number;
}

export interface AuditReportResponse {
  base_url: string;
  discovered_at: string;
  summary: AuditSummary;
  findings: AuditFinding[];
  warnings: string[];
  run_id: number | null;
}

export interface AuditHistoryItem {
  id: number;
  site_url: string;
  summary_status: string;
  created_at: string;
  findings_count: number;
}

export interface AuditHistoryResponse {
  items: AuditHistoryItem[];
}