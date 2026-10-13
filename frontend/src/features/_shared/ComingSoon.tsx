import { Construction } from "lucide-react";

interface ComingSoonProps {
  title: string;
  description?: string;
  phase?: string;
}

export function ComingSoon({
  title,
  description,
  phase,
}: ComingSoonProps): JSX.Element {
  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-4 text-2xl font-semibold text-slate-800">{title}</h1>
      <div className="rounded-lg border border-dashed border-surface-border bg-white p-8 text-center">
        <Construction
          className="mx-auto mb-3 h-10 w-10 text-slate-400"
          aria-hidden="true"
        />
        <p className="mb-1 text-base font-medium text-slate-700">
          This section is planned for a later phase.
        </p>
        {description ? (
          <p className="mb-4 text-sm text-slate-500">{description}</p>
        ) : null}
        {phase ? (
          <span className="inline-block rounded-full bg-brand-light px-3 py-1 text-xs font-medium text-brand-dark">
            {phase}
          </span>
        ) : null}
      </div>
    </div>
  );
}