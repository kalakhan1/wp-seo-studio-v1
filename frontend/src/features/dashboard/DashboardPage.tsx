import { Activity, CheckCircle2, Circle, Cpu, Database } from "lucide-react";

import { LoadingPage } from "@/components/feedback/Loading";
import { useAppStore } from "@/store/appStore";

interface PhaseInfo {
  phase: string;
  label: string;
  status: "done" | "active" | "planned";
}

const PHASES: PhaseInfo[] = [
  { phase: "1", label: "Foundation (backend + frontend)", status: "done" },
  { phase: "2", label: "Connection & capability discovery", status: "done" },
  { phase: "3", label: "Core publishing (product / post / page)", status: "done" },
  { phase: "4", label: "WooCommerce store setup (COD, shipping)", status: "done" },
  { phase: "5", label: "Image presets & archive grid", status: "done" },
  { phase: "6", label: "Rank Math settings manager", status: "done" },
  { phase: "7", label: "Internal linking studio", status: "done" },
  { phase: "8", label: "AI prompt studio", status: "done" },
  { phase: "9", label: "Technical SEO audit", status: "done" },
  { phase: "10", label: "Queue, history, backup", status: "done" },
];

const statusStyles: Record<PhaseInfo["status"], string> = {
  done: "bg-success-light text-success",
  active: "bg-brand-light text-brand-dark",
  planned: "bg-slate-100 text-slate-500",
};

function PhaseIcon({ status }: { status: PhaseInfo["status"] }): JSX.Element {
  if (status === "done") return <CheckCircle2 className="h-4 w-4" aria-hidden="true" />;
  if (status === "active") return <Activity className="h-4 w-4" aria-hidden="true" />;
  return <Circle className="h-4 w-4" aria-hidden="true" />;
}

export function DashboardPage(): JSX.Element {
  const health = useAppStore((s) => s.health);

  if (!health) {
    return <LoadingPage label="Loading dashboard…" />;
  }

  const doneCount = PHASES.filter((p) => p.status === "done").length;
  const totalCount = PHASES.length;
  const progressPct = Math.round((doneCount / totalCount) * 100);

  return (
    <div className="mx-auto max-w-5xl">
      <h1 className="mb-6 text-2xl font-semibold text-slate-800">Dashboard</h1>

      {/* Health card */}
      <section className="mb-6 rounded-lg border border-surface-border bg-white p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-800">
            Application Health
          </h2>
          <span
            className={`rounded-full px-3 py-1 text-xs font-medium capitalize ${
              health.status === "ok"
                ? "bg-success-light text-success"
                : health.status === "degraded"
                  ? "bg-warning-light text-warning"
                  : "bg-danger-light text-danger"
            }`}
          >
            {health.status}
          </span>
        </div>

        <dl className="mb-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-400">
              Mode
            </dt>
            <dd className="font-mono text-slate-800">{health.mode}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-400">
              Version
            </dt>
            <dd className="font-mono text-slate-800">{health.version}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-400">
              Updated
            </dt>
            <dd className="text-slate-800">
              {new Date(health.timestamp).toLocaleTimeString()}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-400">
              Components
            </dt>
            <dd className="text-slate-800">{health.components.length}</dd>
          </div>
        </dl>

        <ul className="divide-y divide-surface-border rounded border border-surface-border">
          {health.components.map((c) => (
            <li key={c.name} className="flex items-center gap-3 px-3 py-2 text-sm">
              {c.name === "database" ? (
                <Database className="h-4 w-4 text-slate-400" aria-hidden="true" />
              ) : (
                <Cpu className="h-4 w-4 text-slate-400" aria-hidden="true" />
              )}
              <span className="w-24 font-medium capitalize text-slate-700">
                {c.name}
              </span>
              <span className="flex-1 text-slate-500">{c.detail}</span>
              <span
                className={`rounded px-2 py-0.5 text-xs font-medium capitalize ${
                  c.status === "ok"
                    ? "bg-success-light text-success"
                    : c.status === "degraded"
                      ? "bg-warning-light text-warning"
                      : "bg-danger-light text-danger"
                }`}
              >
                {c.status}
              </span>
            </li>
          ))}
        </ul>
      </section>

      {/* Phase progress */}
      <section className="rounded-lg border border-surface-border bg-white p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-800">
            Implementation Progress
          </h2>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-600">
              {doneCount} / {totalCount} complete
            </span>
            <span className="rounded-full bg-success-light px-2.5 py-1 text-xs font-medium text-success">
              {progressPct}%
            </span>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mb-4 h-2 w-full overflow-hidden rounded-full bg-surface-muted">
          <div
            className="h-full bg-success transition-all"
            style={{ width: `${progressPct}%` }}
          />
        </div>

        <ul className="space-y-2">
          {PHASES.map((p) => (
            <li
              key={p.phase}
              className="flex items-center gap-3 rounded border border-surface-border px-3 py-2 text-sm"
            >
              <span
                className={`inline-flex h-6 items-center gap-1 rounded-full px-2 text-xs font-medium ${statusStyles[p.status]}`}
              >
                <PhaseIcon status={p.status} />
                <span className="capitalize">{p.status}</span>
              </span>
              <span className="w-16 text-xs uppercase tracking-wide text-slate-400">
                Phase {p.phase}
              </span>
              <span className="flex-1 text-slate-700">{p.label}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}