import { useCallback, useEffect, useState } from "react";
import { History as HistoryIcon, RefreshCw } from "lucide-react";
import { toast } from "sonner";

import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingPage } from "@/components/feedback/Loading";
import { historyApi } from "@/services/historyApi";
import type { HistoryEntry, HistorySummary } from "@/types/history";
import { ApiError } from "@/types/errors";

export function HistoryPage(): JSX.Element {
  const [entries, setEntries] = useState<HistoryEntry[] | null>(null);
  const [summary, setSummary] = useState<HistorySummary | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [list, sum] = await Promise.all([
        historyApi.list({ status: statusFilter || undefined, limit: 100 }),
        historyApi.summary(),
      ]);
      setEntries(list.items);
      setSummary(sum);
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Failed to load history: ${err.message}`);
      } else {
        toast.error("Failed to load history.");
      }
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    void reload();
  }, [reload]);

  if (entries === null) {
    return <LoadingPage label="Loading history…" />;
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold text-slate-800">
            <HistoryIcon className="h-6 w-6 text-slate-400" />
            History and Logs
          </h1>
          <p className="text-sm text-slate-500">
            Local audit trail of every publish and update operation. WordPress
            remains authoritative for the content itself.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded border border-surface-border bg-white px-3 py-2 text-sm"
          >
            <option value="">All statuses</option>
            <option value="success">Success</option>
            <option value="failed">Failed</option>
            <option value="partial">Partial</option>
          </select>
          <button
            type="button"
            onClick={() => void reload()}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded border border-surface-border px-3 py-2 text-sm font-medium text-slate-700 hover:bg-surface-muted disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {summary ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatChip label="Total" value={summary.total} tone="muted" />
          <StatChip label="Success" value={summary.success} tone="success" />
          <StatChip label="Failed" value={summary.failed} tone="danger" />
          <StatChip label="Partial" value={summary.partial} tone="warning" />
        </div>
      ) : null}

      {entries.length === 0 ? (
        <EmptyState
          title="No history yet"
          description="Operations you perform will appear here: create, update, delete, publish, and scheduled posts."
          icon={<HistoryIcon className="h-10 w-10" />}
        />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-surface-border bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-border text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-3 py-2">When</th>
                <th className="px-3 py-2">Object</th>
                <th className="px-3 py-2">Operation</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">WP ID</th>
                <th className="px-3 py-2">Message</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.id} className="border-b border-surface-border/60">
                  <td className="px-3 py-2 text-xs text-slate-500">
                    {new Date(e.created_at).toLocaleString()}
                  </td>
                  <td className="px-3 py-2 text-slate-700">{e.object_type}</td>
                  <td className="px-3 py-2 text-slate-700">{e.operation}</td>
                  <td className="px-3 py-2">
                    <StatusBadge status={e.status} />
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-slate-600">
                    {e.wp_object_id ?? "—"}
                  </td>
                  <td className="px-3 py-2 max-w-[280px] truncate text-xs text-slate-600">
                    {e.message || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function StatChip({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "success" | "warning" | "danger" | "muted";
}): JSX.Element {
  const color =
    tone === "success"
      ? "bg-success-light text-success"
      : tone === "warning"
        ? "bg-warning-light text-warning"
        : tone === "danger"
          ? "bg-danger-light text-danger"
          : "bg-surface-muted text-slate-600";
  return (
    <div className={`rounded-lg px-3 py-2 ${color}`}>
      <p className="text-xs uppercase tracking-wide opacity-80">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }): JSX.Element {
  const map: Record<string, string> = {
    success: "bg-success-light text-success",
    failed: "bg-danger-light text-danger",
    partial: "bg-warning-light text-warning",
  };
  const cls = map[status] ?? "bg-surface-muted text-slate-600";
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}