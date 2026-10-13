import { useCallback, useEffect, useState } from "react";
import { ClipboardCheck, Loader2, Package, Play } from "lucide-react";
import { toast } from "sonner";

import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingPage } from "@/components/feedback/Loading";
import { FindingCard } from "@/features/seo-audit/FindingCard";
import { connectionApi } from "@/services/connectionApi";
import { seoAuditApi } from "@/services/seoAuditApi";
import type { Connection } from "@/types/connection";
import type {
  AuditFinding,
  AuditHistoryItem,
  AuditReportResponse,
  Severity,
} from "@/types/seoAudit";
import { ApiError } from "@/types/errors";

const SEVERITY_ORDER: Severity[] = ["fail", "warn", "info", "pass"];

export function SEOAuditPage(): JSX.Element {
  const [connections, setConnections] = useState<Connection[] | null>(null);
  const [activeConnectionId, setActiveConnectionId] = useState<number | null>(
    null,
  );
  const [report, setReport] = useState<AuditReportResponse | null>(null);
  const [history, setHistory] = useState<AuditHistoryItem[]>([]);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        const res = await connectionApi.list();
        setConnections(res.connections);
        const first = res.connections[0];
        if (first) setActiveConnectionId(first.id);
      } catch {
        toast.error("Failed to load connections.");
        setConnections([]);
      }
    })();
  }, []);

  const loadHistory = useCallback(async () => {
    try {
      const res = await seoAuditApi.history();
      setHistory(res.items);
    } catch {
      setHistory([]);
    }
  }, []);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  const runAudit = async (): Promise<void> => {
    if (activeConnectionId === null) return;
    setRunning(true);
    try {
      const res = await seoAuditApi.run(activeConnectionId);
      setReport(res);
      const failed = res.summary.fail_count;
      const warned = res.summary.warn_count;
      if (failed > 0) {
        toast.error(`Audit complete: ${failed} failure(s).`);
      } else if (warned > 0) {
        toast.warning(`Audit complete: ${warned} warning(s).`);
      } else {
        toast.success("Audit complete: no issues found.");
      }
      await loadHistory();
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Audit failed: ${err.message}`);
      } else {
        toast.error("Audit failed.");
      }
    } finally {
      setRunning(false);
    }
  };

  if (connections === null) {
    return <LoadingPage label="Loading…" />;
  }

  if (connections.length === 0) {
    return (
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-6 text-2xl font-semibold text-slate-800">
          Technical SEO Audit
        </h1>
        <EmptyState
          title="Add a connection first"
          description="The SEO audit requires a WordPress connection."
          icon={<Package className="h-10 w-10" />}
          action={
            <a
              href="/connection"
              className="rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
            >
              Go to Website Connection
            </a>
          }
        />
      </div>
    );
  }

  const grouped: Record<Severity, AuditFinding[]> = {
    fail: [],
    warn: [],
    info: [],
    pass: [],
  };
  if (report) {
    for (const f of report.findings) {
      grouped[f.severity].push(f);
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold text-slate-800">
            <ClipboardCheck className="h-6 w-6 text-slate-400" />
            Technical SEO Audit
          </h1>
          <p className="text-sm text-slate-500">
            Truthful checks against your connected site. Findings show
            evidence and a suggested fix. No claims are made about external
            services unless they are actually connected.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {connections.length > 1 ? (
            <select
              value={activeConnectionId?.toString() ?? ""}
              onChange={(e) => setActiveConnectionId(Number(e.target.value))}
              className="rounded border border-surface-border bg-white px-3 py-2 text-sm"
            >
              {connections.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          ) : null}
          <button
            type="button"
            onClick={() => void runAudit()}
            disabled={running}
            className="inline-flex items-center gap-2 rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
          >
            {running ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            {running ? "Running audit…" : "Run audit"}
          </button>
        </div>
      </div>

      {report === null ? (
        <EmptyState
          title="No audit yet"
          description="Click Run audit to check HTTPS, sitemap, robots.txt, permalinks, media alt text, and more."
          icon={<ClipboardCheck className="h-10 w-10" />}
        />
      ) : (
        <>
          {/* Summary */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <SummaryStat label="Fail" value={report.summary.fail_count} tone="danger" />
            <SummaryStat label="Warn" value={report.summary.warn_count} tone="warning" />
            <SummaryStat label="Info" value={report.summary.info_count} tone="muted" />
            <SummaryStat label="Pass" value={report.summary.pass_count} tone="success" />
          </div>

          {report.warnings.length > 0 ? (
            <div className="rounded-lg border border-warning bg-warning-light/30 p-4">
              <p className="mb-2 text-sm font-medium text-warning">Notes</p>
              <ul className="ml-4 list-disc text-xs text-slate-700">
                {report.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {/* Findings */}
          {SEVERITY_ORDER.map((sev) => {
            const items = grouped[sev];
            if (items.length === 0) return null;
            const heading =
              sev === "info"
                ? "Informational"
                : sev === "pass"
                  ? "Passed"
                  : sev === "warn"
                    ? "Warnings"
                    : "Failures";
            return (
              <section key={sev} className="space-y-3">
                <h2 className="text-base font-semibold text-slate-800">
                  {heading} ({items.length})
                </h2>
                {items.map((f) => (
                  <FindingCard key={f.check_id} finding={f} />
                ))}
              </section>
            );
          })}
        </>
      )}

      {/* History */}
      {history.length > 0 ? (
        <section className="rounded-lg border border-surface-border bg-white p-5">
          <h2 className="mb-3 text-base font-semibold text-slate-800">
            Recent audits
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-border text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-3">When</th>
                  <th className="py-2 pr-3">Site</th>
                  <th className="py-2 pr-3">Status</th>
                  <th className="py-2 pr-3">Findings</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h) => (
                  <tr key={h.id} className="border-b border-surface-border/60">
                    <td className="py-2 pr-3 text-slate-700">
                      {new Date(h.created_at).toLocaleString()}
                    </td>
                    <td className="py-2 pr-3 font-mono text-xs text-slate-600">
                      {h.site_url}
                    </td>
                    <td className="py-2 pr-3">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                          h.summary_status === "ok"
                            ? "bg-success-light text-success"
                            : h.summary_status === "warnings"
                              ? "bg-warning-light text-warning"
                              : "bg-danger-light text-danger"
                        }`}
                      >
                        {h.summary_status}
                      </span>
                    </td>
                    <td className="py-2 pr-3 text-slate-700">
                      {h.findings_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </div>
  );
}

function SummaryStat({
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
      ? "text-success"
      : tone === "warning"
        ? "text-warning"
        : tone === "danger"
          ? "text-danger"
          : "text-slate-600";
  return (
    <div className="rounded-lg border border-surface-border bg-white px-4 py-3">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`text-2xl font-semibold ${color}`}>{value}</p>
    </div>
  );
}