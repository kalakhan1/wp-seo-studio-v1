import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";

import type { RankMathCapabilityStatus } from "@/types/rankmathSettings";

interface RankMathStatusCardProps {
  status: RankMathCapabilityStatus;
}

export function RankMathStatusCard({
  status,
}: RankMathStatusCardProps): JSX.Element {
  const tone = !status.plugin_available
    ? "danger"
    : !status.rank_math_active
      ? "warning"
      : "success";

  const bg =
    tone === "success"
      ? "border-success bg-success-light/30"
      : tone === "warning"
        ? "border-warning bg-warning-light/30"
        : "border-danger bg-danger-light/30";

  const icon =
    tone === "success" ? (
      <CheckCircle2 className="h-5 w-5 text-success" />
    ) : tone === "warning" ? (
      <AlertTriangle className="h-5 w-5 text-warning" />
    ) : (
      <XCircle className="h-5 w-5 text-danger" />
    );

  const label = !status.plugin_available
    ? "Companion plugin not detected"
    : status.rank_math_active
      ? "Rank Math active"
      : "Rank Math inactive";

  return (
    <div className={`rounded-lg border ${bg} p-5`}>
      <div className="mb-3 flex items-center gap-2">
        {icon}
        <h2 className="text-base font-semibold text-slate-800">{label}</h2>
      </div>

      {status.reason ? (
        <p className="mb-3 text-sm text-slate-700">{status.reason}</p>
      ) : null}

      <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-400">
            Plugin
          </dt>
          <dd className="text-slate-800">
            {status.plugin_available ? "installed" : "not installed"}
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-400">
            Rank Math
          </dt>
          <dd className="text-slate-800">
            {status.rank_math_active ? "active" : "inactive"}
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-400">
            Version
          </dt>
          <dd className="font-mono text-slate-800">
            {status.version || "—"}
          </dd>
        </div>
      </dl>
    </div>
  );
}