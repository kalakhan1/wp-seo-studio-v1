import { AlertTriangle } from "lucide-react";

import type { DiscoveredSizesResponse } from "@/types/imagePresets";

interface DiscoveredSizesTableProps {
  data: DiscoveredSizesResponse | null;
  loading: boolean;
  onRefresh: () => void;
}

export function DiscoveredSizesTable({
  data,
  loading,
  onRefresh,
}: DiscoveredSizesTableProps): JSX.Element {
  return (
    <div className="rounded-lg border border-surface-border bg-white p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-800">
            Registered WordPress Sizes
          </h2>
          <p className="text-xs text-slate-500">
            Discovered from an existing media item. Not a suggestion —
            what WordPress and active plugins actually registered.
          </p>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          className="rounded border border-surface-border px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-surface-muted disabled:opacity-50"
        >
          {loading ? "Discovering…" : "Discover"}
        </button>
      </div>

      {data === null ? (
        <p className="py-4 text-sm text-slate-500">
          Click Discover to inspect the connected site.
        </p>
      ) : data.sizes.length === 0 ? (
        <p className="py-4 text-sm text-slate-500">
          No registered sizes returned.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-border text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-3">Name</th>
                <th className="py-2 pr-3">Dimensions</th>
                <th className="py-2 pr-3">Crop</th>
              </tr>
            </thead>
            <tbody>
              {data.sizes.map((s) => (
                <tr key={s.name} className="border-b border-surface-border/60">
                  <td className="py-2 pr-3 font-mono text-slate-800">
                    {s.name}
                  </td>
                  <td className="py-2 pr-3 font-mono text-slate-700">
                    {s.width} × {s.height}
                  </td>
                  <td className="py-2 pr-3 text-slate-700">
                    {s.crop ? "yes" : "no"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && data.warnings.length > 0 ? (
        <div className="mt-4 rounded border border-warning bg-warning-light/30 p-3">
          <div className="mb-1 flex items-center gap-2 text-sm font-semibold text-warning">
            <AlertTriangle className="h-4 w-4" />
            Warnings
          </div>
          <ul className="ml-6 list-disc space-y-0.5 text-xs text-slate-700">
            {data.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}