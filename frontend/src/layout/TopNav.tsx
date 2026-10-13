import { Menu } from "lucide-react";

import { useAppStore } from "@/store/appStore";

interface TopNavProps {
  onToggleSidebar: () => void;
}

const STATUS_COLORS = {
  ok: "bg-success",
  degraded: "bg-warning",
  failed: "bg-danger",
  unknown: "bg-slate-300",
} as const;

export function TopNav({ onToggleSidebar }: TopNavProps): JSX.Element {
  const health = useAppStore((s) => s.health);
  const settings = useAppStore((s) => s.settings);

  const status = health?.status ?? "unknown";
  const mode = health?.mode ?? settings?.app_mode ?? "—";
  const statusColor = STATUS_COLORS[status];

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-surface-border bg-white px-4">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onToggleSidebar}
          className="rounded p-1 text-slate-600 hover:bg-surface-muted lg:hidden"
          aria-label="Toggle navigation"
        >
          <Menu className="h-5 w-5" aria-hidden="true" />
        </button>
        <div>
          <p className="text-sm font-semibold text-slate-800">
            WP SEO Control Studio
          </p>
          <p className="text-[11px] text-slate-500">
            WordPress + WooCommerce + Rank Math
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <span
          className="hidden items-center gap-1.5 rounded-full bg-surface-muted px-2.5 py-1 text-xs font-medium text-slate-600 sm:inline-flex"
          title="Active runtime mode"
        >
          <span className="text-[10px] uppercase tracking-wide text-slate-400">
            Mode
          </span>
          <span className="font-mono">{mode}</span>
        </span>

        <span
          className="inline-flex items-center gap-1.5 rounded-full bg-surface-muted px-2.5 py-1 text-xs font-medium text-slate-600"
          title={health ? `Health: ${status}` : "Health unknown"}
        >
          <span className={`h-2 w-2 rounded-full ${statusColor}`} aria-hidden="true" />
          <span className="capitalize">{status}</span>
        </span>
      </div>
    </header>
  );
}