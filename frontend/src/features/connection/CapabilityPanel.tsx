import { CheckCircle2, AlertTriangle, XCircle, HelpCircle } from "lucide-react";

import type {
  CapabilityItem,
  CapabilityReport,
  CapabilityStatus,
} from "@/types/capability";

interface CapabilityPanelProps {
  report: CapabilityReport;
}

const STATUS_LABEL: Record<CapabilityStatus, string> = {
  supported: "Supported",
  read_only: "Read-only",
  requires_elevated: "Requires elevated permission",
  requires_plugin: "Requires companion plugin",
  requires_manual_setup: "Requires manual setup",
  not_verified: "Not verified",
  unsupported: "Unsupported",
};

const STATUS_STYLE: Record<CapabilityStatus, string> = {
  supported: "bg-success-light text-success",
  read_only: "bg-brand-light text-brand-dark",
  requires_elevated: "bg-warning-light text-warning",
  requires_plugin: "bg-warning-light text-warning",
  requires_manual_setup: "bg-warning-light text-warning",
  not_verified: "bg-slate-100 text-slate-600",
  unsupported: "bg-danger-light text-danger",
};

function StatusIcon({ status }: { status: CapabilityStatus }): JSX.Element {
  if (status === "supported") return <CheckCircle2 className="h-3.5 w-3.5" />;
  if (status === "unsupported") return <XCircle className="h-3.5 w-3.5" />;
  if (status === "not_verified") return <HelpCircle className="h-3.5 w-3.5" />;
  return <AlertTriangle className="h-3.5 w-3.5" />;
}

export function CapabilityPanel({ report }: CapabilityPanelProps): JSX.Element {
  const grouped = report.capabilities.reduce<Record<string, CapabilityItem[]>>(
    (acc, item) => {
      const list = acc[item.category] ?? [];
      list.push(item);
      acc[item.category] = list;
      return acc;
    },
    {},
  );

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="rounded-lg border border-surface-border bg-white p-5">
        <h3 className="mb-3 text-base font-semibold text-slate-800">
          Capability Summary
        </h3>
        <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <SummaryStat label="Supported" value={report.summary.supported} tone="success" />
          <SummaryStat label="Requires action" value={
            report.summary.requires_elevated
            + report.summary.requires_plugin
            + report.summary.requires_manual_setup
          } tone="warning" />
          <SummaryStat label="Not verified" value={report.summary.not_verified} tone="muted" />
          <SummaryStat label="Unsupported" value={report.summary.unsupported} tone="danger" />
        </div>
        {report.warnings.length > 0 ? (
          <ul className="mt-4 ml-4 list-disc space-y-1 text-xs text-warning">
            {report.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        ) : null}
      </div>

      {/* Site & User */}
      <div className="rounded-lg border border-surface-border bg-white p-5">
        <h3 className="mb-3 text-base font-semibold text-slate-800">
          Site &amp; User
        </h3>
        <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-400">
              Site name
            </dt>
            <dd className="font-mono text-slate-800">
              {report.site_info?.name ?? "—"}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-400">
              Timezone
            </dt>
            <dd className="font-mono text-slate-800">
              {report.site_info?.timezone_string || "—"}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-400">
              Current user
            </dt>
            <dd className="font-mono text-slate-800">
              {report.current_user?.name ?? "—"}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-400">
              Roles
            </dt>
            <dd className="font-mono text-slate-800">
              {report.current_user?.roles.join(", ") || "—"}
            </dd>
          </div>
        </dl>
      </div>

      {/* Rank Math */}
      <div className="rounded-lg border border-surface-border bg-white p-5">
        <h3 className="mb-3 text-base font-semibold text-slate-800">Rank Math</h3>
        <ul className="space-y-1 text-sm text-slate-700">
          <li>
            Plugin detected:{" "}
            <span className="font-mono">
              {report.rankmath.plugin_detected ? "yes" : "not conclusive"}
            </span>
          </li>
          <li>
            Companion plugin detected:{" "}
            <span className="font-mono">
              {report.rankmath.companion_plugin_detected ? "yes" : "no"}
            </span>
          </li>
          <li>
            Companion settings reachable:{" "}
            <span className="font-mono">
              {report.rankmath.companion_settings_available ? "yes" : "no"}
            </span>
          </li>
        </ul>
        {report.rankmath.reason ? (
          <p className="mt-3 text-xs text-slate-500">{report.rankmath.reason}</p>
        ) : null}
      </div>

      {/* Post types and Taxonomies */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-lg border border-surface-border bg-white p-5">
          <h3 className="mb-3 text-base font-semibold text-slate-800">
            Post Types ({report.post_types.length})
          </h3>
          <ul className="space-y-1 text-sm">
            {report.post_types.map((pt) => (
              <li key={pt.slug} className="flex items-center justify-between">
                <span className="font-mono text-slate-800">{pt.slug}</span>
                <span className="text-xs text-slate-500">
                  {pt.rest_namespace}/{pt.rest_base}
                </span>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-lg border border-surface-border bg-white p-5">
          <h3 className="mb-3 text-base font-semibold text-slate-800">
            Taxonomies ({report.taxonomies.length})
          </h3>
          <ul className="space-y-1 text-sm">
            {report.taxonomies.map((t) => (
              <li key={t.slug} className="flex items-center justify-between">
                <span className="font-mono text-slate-800">{t.slug}</span>
                <span className="text-xs text-slate-500">
                  {t.rest_namespace}/{t.rest_base}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Capabilities by category */}
      {Object.entries(grouped).map(([category, items]) => (
        <div key={category} className="rounded-lg border border-surface-border bg-white p-5">
          <h3 className="mb-3 text-base font-semibold capitalize text-slate-800">
            {category}
          </h3>
          <ul className="space-y-2">
            {items.map((item) => (
              <li
                key={item.key}
                className="rounded border border-surface-border p-3 text-sm"
              >
                <div className="mb-1 flex flex-wrap items-center gap-2">
                  <span className="font-medium text-slate-800">{item.label}</span>
                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLE[item.status]}`}
                  >
                    <StatusIcon status={item.status} />
                    {STATUS_LABEL[item.status]}
                  </span>
                  <span className="ml-auto font-mono text-xs text-slate-400">
                    {item.method} {item.endpoint}
                  </span>
                </div>
                {item.reason ? (
                  <p className="text-xs text-slate-500">{item.reason}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ))}
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
  tone: "success" | "warning" | "muted" | "danger";
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
    <div className="rounded border border-surface-border px-3 py-2">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`text-lg font-semibold ${color}`}>{value}</p>
    </div>
  );
}