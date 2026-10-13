import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
}

export function EmptyState({
  title,
  description,
  icon,
  action,
}: EmptyStateProps): JSX.Element {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-surface-border bg-white px-6 py-12 text-center">
      {icon ? <div className="mb-3 text-slate-400">{icon}</div> : null}
      <h3 className="mb-1 text-base font-semibold text-slate-800">{title}</h3>
      {description ? (
        <p className="mb-4 max-w-md text-sm text-slate-500">{description}</p>
      ) : null}
      {action ? <div>{action}</div> : null}
    </div>
  );
}