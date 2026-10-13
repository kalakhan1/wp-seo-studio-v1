import { ArrowRight, CheckCircle2, Info, XCircle, AlertTriangle } from "lucide-react";
import { Link } from "react-router-dom";

import type { AuditFinding, Severity } from "@/types/seoAudit";

const SEVERITY_STYLE: Record<Severity, string> = {
  pass: "bg-success-light text-success border-success",
  warn: "bg-warning-light text-warning border-warning",
  fail: "bg-danger-light text-danger border-danger",
  info: "bg-slate-100 text-slate-600 border-surface-border",
};

const SEVERITY_LABEL: Record<Severity, string> = {
  pass: "Pass",
  warn: "Warning",
  fail: "Fail",
  info: "Info",
};

function SeverityIcon({ severity }: { severity: Severity }): JSX.Element {
  if (severity === "pass") return <CheckCircle2 className="h-4 w-4" />;
  if (severity === "warn") return <AlertTriangle className="h-4 w-4" />;
  if (severity === "fail") return <XCircle className="h-4 w-4" />;
  return <Info className="h-4 w-4" />;
}

export function FindingCard({ finding }: { finding: AuditFinding }): JSX.Element {
  return (
    <div className={`rounded-lg border bg-white p-4 ${SEVERITY_STYLE[finding.severity].split(" ")[2] ?? ""}`}>
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span
          className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${SEVERITY_STYLE[finding.severity]}`}
        >
          <SeverityIcon severity={finding.severity} />
          {SEVERITY_LABEL[finding.severity]}
        </span>
        <span className="inline-flex items-center rounded-full bg-surface-muted px-2 py-0.5 text-xs font-medium text-slate-600">
          {finding.category}
        </span>
        <span className="text-sm font-semibold text-slate-800">
          {finding.label}
        </span>
        <span className="font-mono text-[10px] text-slate-400">
          {finding.check_id}
        </span>
      </div>

      <p className="mb-2 text-sm text-slate-700">{finding.message}</p>

      {finding.suggested_fix ? (
        <p className="mb-2 text-xs text-slate-600">
          <span className="font-medium text-slate-700">Suggested fix: </span>
          {finding.suggested_fix}
        </p>
      ) : null}

      {Object.keys(finding.evidence).length > 0 ? (
        <pre className="mb-2 max-h-40 overflow-auto rounded bg-slate-900 p-2 text-[11px] text-slate-100">
          {JSON.stringify(finding.evidence, null, 2)}
        </pre>
      ) : null}

      {finding.affected_urls.length > 0 ? (
        <ul className="mb-2 ml-4 list-disc text-xs text-slate-600">
          {finding.affected_urls.slice(0, 5).map((u) => (
            <li key={u} className="font-mono">
              {u}
            </li>
          ))}
        </ul>
      ) : null}

      {finding.action_path ? (
        <div className="flex justify-end">
          <Link
            to={finding.action_path}
            className="inline-flex items-center gap-1 rounded border border-surface-border px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-surface-muted"
          >
            Open
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      ) : null}
    </div>
  );
}