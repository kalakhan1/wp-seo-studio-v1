import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";

import type { CODStatus } from "@/types/wcGateway";

interface CODStatusCardProps {
  status: CODStatus;
}

export function CODStatusCard({ status }: CODStatusCardProps): JSX.Element {
  const tone = !status.available
    ? "danger"
    : status.enabled
      ? "success"
      : "warning";

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

  const label = !status.available
    ? "COD gateway not found"
    : status.enabled
      ? "COD enabled"
      : "COD disabled";

  return (
    <div className={`rounded-lg border ${bg} p-5`}>
      <div className="mb-3 flex items-center gap-2">
        {icon}
        <h2 className="text-base font-semibold text-slate-800">{label}</h2>
      </div>

      <dl className="mb-3 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-400">
            Available
          </dt>
          <dd className="text-slate-800">
            {status.available ? "yes" : "no"}
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-400">
            Enabled
          </dt>
          <dd className="text-slate-800">
            {status.enabled ? "yes" : "no"}
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-400">
            Shipping zones
          </dt>
          <dd className="text-slate-800">
            {status.shipping_zones_available ? "configured" : "none"}
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-400">
            Virtual products
          </dt>
          <dd className="text-slate-800">
            {status.enable_for_virtual ? "allowed" : "excluded"}
          </dd>
        </div>
      </dl>

      {status.available ? (
        <div className="mb-3 space-y-1 text-sm">
          <p>
            <span className="text-slate-500">Title:</span>{" "}
            <span className="font-mono text-slate-800">
              {status.title || "—"}
            </span>
          </p>
          <p>
            <span className="text-slate-500">Description:</span>{" "}
            <span className="text-slate-800">
              {status.description || "—"}
            </span>
          </p>
          <p>
            <span className="text-slate-500">Instructions:</span>{" "}
            <span className="text-slate-800">
              {status.instructions || "—"}
            </span>
          </p>
        </div>
      ) : null}

      {status.warnings.length > 0 ? (
        <ul className="ml-4 list-disc space-y-1 text-sm text-slate-700">
          {status.warnings.map((w, i) => (
            <li key={i}>{w}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}