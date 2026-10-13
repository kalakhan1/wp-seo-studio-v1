import type { LucideIcon } from "lucide-react";
import { ArrowRight, CheckCircle2, Circle, XCircle } from "lucide-react";
import { Link } from "react-router-dom";

export type StepStatus = "ok" | "warning" | "missing" | "unknown";

interface SetupStepCardProps {
  number: number;
  title: string;
  description: string;
  status: StepStatus;
  icon: LucideIcon;
  detail?: string;
  warnings?: string[];
  ctaLabel: string;
  ctaTo: string;
}

const STATUS_STYLE: Record<StepStatus, string> = {
  ok: "bg-success-light text-success",
  warning: "bg-warning-light text-warning",
  missing: "bg-danger-light text-danger",
  unknown: "bg-slate-100 text-slate-500",
};

const STATUS_LABEL: Record<StepStatus, string> = {
  ok: "Complete",
  warning: "Action recommended",
  missing: "Action required",
  unknown: "Not verified",
};

function StatusIcon({ status }: { status: StepStatus }): JSX.Element {
  if (status === "ok") return <CheckCircle2 className="h-4 w-4" />;
  if (status === "missing") return <XCircle className="h-4 w-4" />;
  return <Circle className="h-4 w-4" />;
}

export function SetupStepCard({
  number,
  title,
  description,
  status,
  icon: Icon,
  detail,
  warnings,
  ctaLabel,
  ctaTo,
}: SetupStepCardProps): JSX.Element {
  const warnList = warnings ?? [];

  return (
    <div className="rounded-lg border border-surface-border bg-white p-5">
      <div className="mb-3 flex items-start gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-light text-sm font-semibold text-brand-dark">
          {number}
        </div>
        <div className="flex-1">
          <div className="mb-1 flex flex-wrap items-center gap-2">
            <Icon className="h-4 w-4 text-slate-400" />
            <h3 className="font-semibold text-slate-800">{title}</h3>
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLE[status]}`}
            >
              <StatusIcon status={status} />
              {STATUS_LABEL[status]}
            </span>
          </div>
          <p className="text-sm text-slate-600">{description}</p>
          {detail ? (
            <p className="mt-1 font-mono text-xs text-slate-500">{detail}</p>
          ) : null}
        </div>
      </div>

      {warnList.length > 0 ? (
        <ul className="mb-3 ml-11 list-disc space-y-0.5 text-xs text-warning">
          {warnList.map((w, i) => (
            <li key={i}>{w}</li>
          ))}
        </ul>
      ) : null}

      <div className="flex justify-end">
        <Link
          to={ctaTo}
          className="inline-flex items-center gap-1.5 rounded border border-surface-border px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-surface-muted"
        >
          {ctaLabel}
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>
    </div>
  );
}