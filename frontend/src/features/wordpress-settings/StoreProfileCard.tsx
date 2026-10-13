import { AlertTriangle, CheckCircle2, Circle, XCircle } from "lucide-react";

import type {
  ChecklistItem,
  ChecklistStatus,
  StoreProfileResponse,
} from "@/types/wcSettings";

interface StoreProfileCardProps {
  data: StoreProfileResponse;
}

const STATUS_STYLE: Record<ChecklistStatus, string> = {
  ok: "bg-success-light text-success",
  recommended: "bg-warning-light text-warning",
  missing: "bg-danger-light text-danger",
};

function StatusIcon({ status }: { status: ChecklistStatus }): JSX.Element {
  if (status === "ok") return <CheckCircle2 className="h-4 w-4" />;
  if (status === "missing") return <XCircle className="h-4 w-4" />;
  return <Circle className="h-4 w-4" />;
}

export function StoreProfileCard({ data }: StoreProfileCardProps): JSX.Element {
  const { profile, checklist, warnings } = data;

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="rounded-lg border border-surface-border bg-white p-5">
        <div className="mb-4 flex items-start justify-between">
          <h2 className="text-base font-semibold text-slate-800">
            Store Profile
          </h2>
          <div className="flex gap-2 text-xs">
            <span className="rounded-full bg-success-light px-2.5 py-1 font-medium text-success">
              {checklist.complete} ok
            </span>
            <span className="rounded-full bg-warning-light px-2.5 py-1 font-medium text-warning">
              {checklist.recommended} recommended
            </span>
            <span className="rounded-full bg-danger-light px-2.5 py-1 font-medium text-danger">
              {checklist.missing} missing
            </span>
          </div>
        </div>

        <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-400">
              Store address
            </dt>
            <dd className="truncate text-slate-800" title={profile.address.address_1}>
              {profile.address.address_1 || "—"}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-400">
              City
            </dt>
            <dd className="text-slate-800">{profile.address.city || "—"}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-400">
              Country / State
            </dt>
            <dd className="font-mono text-slate-800">
              {profile.address.country_state_raw || "—"}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-400">
              Currency
            </dt>
            <dd className="font-mono text-slate-800">
              {profile.currency || "—"}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-400">
              Weight unit
            </dt>
            <dd className="font-mono text-slate-800">
              {profile.weight_unit || "—"}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-400">
              Dimension unit
            </dt>
            <dd className="font-mono text-slate-800">
              {profile.dimension_unit || "—"}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-400">
              Guest checkout
            </dt>
            <dd className="text-slate-800">
              {profile.guest_checkout_enabled ? "enabled" : "disabled"}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-400">
              Taxes
            </dt>
            <dd className="text-slate-800">
              {profile.tax_enabled ? "enabled" : "disabled"}
            </dd>
          </div>
        </dl>
      </div>

      {/* Warnings */}
      {warnings.length > 0 ? (
        <div className="rounded-lg border border-warning bg-warning-light/30 p-4">
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-warning">
            <AlertTriangle className="h-4 w-4" />
            Warnings
          </div>
          <ul className="ml-6 list-disc space-y-1 text-sm text-slate-700">
            {warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {/* Checklist */}
      <div className="rounded-lg border border-surface-border bg-white p-5">
        <h3 className="mb-3 text-base font-semibold text-slate-800">
          Store Completeness Checklist
        </h3>
        <ul className="divide-y divide-surface-border rounded border border-surface-border">
          {checklist.items.map((item) => (
            <ChecklistRow key={item.key} item={item} />
          ))}
        </ul>
      </div>
    </div>
  );
}

function ChecklistRow({ item }: { item: ChecklistItem }): JSX.Element {
  return (
    <li className="flex items-start gap-3 px-3 py-2 text-sm">
      <span
        className={`mt-0.5 inline-flex h-6 items-center gap-1 rounded-full px-2 text-xs font-medium ${STATUS_STYLE[item.status]}`}
      >
        <StatusIcon status={item.status} />
        <span className="capitalize">{item.status}</span>
      </span>
      <div className="flex-1">
        <p className="font-medium text-slate-800">{item.label}</p>
        {item.message ? (
          <p className="text-xs text-slate-500">{item.message}</p>
        ) : null}
        {item.status === "ok" && item.current_value ? (
          <p className="font-mono text-xs text-slate-600">
            {item.current_value}
          </p>
        ) : null}
        {item.status !== "ok" && item.suggested_value ? (
          <p className="text-xs text-slate-500">
            Suggested:{" "}
            <span className="font-mono">{item.suggested_value}</span>
          </p>
        ) : null}
      </div>
    </li>
  );
}