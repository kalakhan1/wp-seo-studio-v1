interface LoadingProps {
  label?: string;
  size?: "sm" | "md" | "lg";
}

const sizeMap = {
  sm: "h-4 w-4 border-2",
  md: "h-6 w-6 border-2",
  lg: "h-10 w-10 border-4",
} as const;

export function Loading({ label, size = "md" }: LoadingProps): JSX.Element {
  return (
    <div className="flex items-center gap-3" role="status" aria-live="polite">
      <span
        className={`${sizeMap[size]} animate-spin rounded-full border-brand border-t-transparent`}
        aria-hidden="true"
      />
      {label ? <span className="text-sm text-slate-600">{label}</span> : null}
    </div>
  );
}

export function LoadingPage({ label = "Loading…" }: { label?: string }): JSX.Element {
  return (
    <div className="flex min-h-[200px] items-center justify-center">
      <Loading label={label} size="lg" />
    </div>
  );
}