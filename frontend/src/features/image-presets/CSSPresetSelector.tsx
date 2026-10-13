import { CheckCircle2 } from "lucide-react";

import type { CSSPreset } from "@/types/imagePresets";

interface CSSPresetSelectorProps {
  presets: CSSPreset[];
  selectedKey: string | null;
  onSelect: (preset: CSSPreset) => void;
  disabled?: boolean;
}

export function CSSPresetSelector({
  presets,
  selectedKey,
  onSelect,
  disabled = false,
}: CSSPresetSelectorProps): JSX.Element {
  return (
    <div className="mb-4">
      <p className="mb-1 text-sm font-medium text-slate-700">
        Display preset
      </p>
      <p className="mb-3 text-xs text-slate-500">
        These presets only affect CSS in the browser. They do not modify
        WordPress image sizes.
      </p>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {presets.map((p) => {
          const selected = p.key === selectedKey;
          const aspect = p.aspect_ratio === "custom" ? "1:1" : p.aspect_ratio;
          return (
            <button
              key={p.key}
              type="button"
              onClick={() => onSelect(p)}
              disabled={disabled}
              className={`flex flex-col items-start gap-3 rounded-lg border p-3 text-left transition-colors ${
                selected
                  ? "border-brand bg-brand-light/40"
                  : "border-surface-border bg-white hover:bg-surface-muted"
              } disabled:cursor-not-allowed disabled:opacity-50`}
            >
              <div className="flex w-full items-center justify-between">
                <span className="text-sm font-medium text-slate-800">
                  {p.label}
                </span>
                {selected ? (
                  <CheckCircle2 className="h-4 w-4 text-brand" />
                ) : null}
              </div>
              <div
                className="w-full rounded"
                style={{
                  aspectRatio: aspect.replace(":", " / "),
                  backgroundColor: p.background,
                  borderRadius: p.border_radius,
                  border: "1px solid #e2e8f0",
                }}
              />
              <div className="text-xs text-slate-500">
                <p>
                  <span className="font-mono">{p.aspect_ratio}</span> ·{" "}
                  <span className="font-mono">{p.object_fit}</span>
                </p>
                {p.description ? (
                  <p className="mt-1 text-slate-500">{p.description}</p>
                ) : null}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}