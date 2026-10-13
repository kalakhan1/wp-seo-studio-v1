import { useCallback, useEffect, useState } from "react";
import { ListChecks, RefreshCw, RotateCcw, XCircle } from "lucide-react";
import { toast } from "sonner";

import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingPage } from "@/components/feedback/Loading";
import { queueApi } from "@/services/queueApi";
import type { QueueJob, QueueSummary } from "@/types/queue";
import { ApiError } from "@/types/errors";

export function QueuePage(): JSX.Element {
  const [jobs, setJobs] = useState<QueueJob[] | null>(null);
  const [summary, setSummary] = useState<QueueSummary | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [list, sum] = await Promise.all([
        queueApi.list({ status: statusFilter || undefined, limit: 100 }),
        queueApi.summary(),
      ]);
      setJobs(list.items);
      setSummary(sum);
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Failed to load queue: ${err.message}`);
      } else {
        toast.error("Failed to load queue.");
      }
      setJobs([]);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const handleCancel = async (job: QueueJob): Promise<void> => {
    try {
      await queueApi.cancel(job.id);
      toast.success("Job cancelled.");
      void reload();
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Cancel failed: ${err.message}`);
      } else {
        toast.error("Cancel failed.");
      }
    }
  };

  const handleRetry = async (job: QueueJob): Promise<void> => {
    try {
      await queueApi.retry(job.id);
      toast.success("Job queued for retry.");
      void reload();
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Retry failed: ${err.message}`);
      } else {
        toast.error("Retry failed.");
      }
    }
  };

  if (jobs === null) {
    return <LoadingPage label="Loading queue…" />;
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold text-slate-800">
            <ListChecks className="h-6 w-6 text-slate-400" />
            Publishing Queue
          </h1>
          <p className="text-sm text-slate-500">
            Jobs are recorded locally. Background execution is not part of
            this phase — this page gives you visibility and control over
            queued operations.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded border border-surface-border bg-white px-3 py-2 text-sm"
          >
            <option value="">All statuses</option>
            <option value="pending">Pending</option>
            <option value="running">Running</option>
            <option value="success">Success</option>
            <option value="failed">Failed</option>
            <option value="partial">Partial</option>
            <option value="cancelled">Cancelled</option>
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
        <div className="grid grid-cols-3 gap-3 sm:grid-cols-6">
          <StatChip label="Pending" value={summary.pending} tone="muted" />
          <StatChip label="Running" value={summary.running} tone="brand" />
          <StatChip label="Success" value={summary.success} tone="success" />
          <StatChip label="Failed" value={summary.failed} tone="danger" />
          <StatChip label="Partial" value={summary.partial} tone="warning" />
          <StatChip label="Cancelled" value={summary.cancelled} tone="muted" />
        </div>
      ) : null}

      {jobs.length === 0 ? (
        <EmptyState
          title="No jobs yet"
          description="Queued operations appear here. Nothing is currently pending."
          icon={<ListChecks className="h-10 w-10" />}
        />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-surface-border bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-border text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-3 py-2">Job</th>
                <th className="px-3 py-2">Type</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Progress</th>
                <th className="px-3 py-2">Error</th>
                <th className="px-3 py-2">Created</th>
                <th className="px-3 py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr
                  key={job.id}
                  className="border-b border-surface-border/60"
                >
                  <td className="px-3 py-2 font-mono text-xs text-slate-600">
                    {job.job_id.slice(0, 8)}
                  </td>
                  <td className="px-3 py-2 text-slate-700">{job.job_type}</td>
                  <td className="px-3 py-2">
                    <StatusBadge status={job.status} />
                  </td>
                  <td className="px-3 py-2 text-slate-700">
                    {job.progress}%
                  </td>
                  <td className="px-3 py-2 max-w-[200px] truncate text-xs text-danger">
                    {job.error || "—"}
                  </td>
                  <td className="px-3 py-2 text-xs text-slate-500">
                    {new Date(job.created_at).toLocaleString()}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {job.status === "pending" || job.status === "retrying" ? (
                      <button
                        type="button"
                        onClick={() => void handleCancel(job)}
                        className="inline-flex items-center gap-1 rounded border border-danger px-2 py-1 text-xs font-medium text-danger hover:bg-danger-light"
                      >
                        <XCircle className="h-3 w-3" />
                        Cancel
                      </button>
                    ) : job.status === "failed" ||
                      job.status === "partial" ||
                      job.status === "cancelled" ? (
                      <button
                        type="button"
                        onClick={() => void handleRetry(job)}
                        className="inline-flex items-center gap-1 rounded border border-brand px-2 py-1 text-xs font-medium text-brand hover:bg-brand-light"
                      >
                        <RotateCcw className="h-3 w-3" />
                        Retry
                      </button>
                    ) : (
                      <span className="text-xs text-slate-400">—</span>
                    )}
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
  tone: "success" | "warning" | "danger" | "brand" | "muted";
}): JSX.Element {
  const color =
    tone === "success"
      ? "bg-success-light text-success"
      : tone === "warning"
        ? "bg-warning-light text-warning"
        : tone === "danger"
          ? "bg-danger-light text-danger"
          : tone === "brand"
            ? "bg-brand-light text-brand-dark"
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
    pending: "bg-surface-muted text-slate-600",
    running: "bg-brand-light text-brand-dark",
    success: "bg-success-light text-success",
    failed: "bg-danger-light text-danger",
    partial: "bg-warning-light text-warning",
    cancelled: "bg-surface-muted text-slate-500",
    retrying: "bg-warning-light text-warning",
  };
  const cls = map[status] ?? "bg-surface-muted text-slate-600";
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}

