import { useId } from "react";

import type { AspectRatio } from "@/types/imagePresets";

interface AspectRatioSelectorProps {
  value: AspectRatio;
  onChange: (next: AspectRatio) => void;
  customWidth: number;
  customHeight: number;
  onCustomWidthChange: (n: number) => void;
  onCustomHeightChange: (n: number) => void;
  disabled?: boolean;
}

const PRESETS: AspectRatio[] = [
  "1:1",
  "4:5",
  "3:4",
  "4:3",
  "3:2",
  "16:9",
  "2:3",
];

export function AspectRatioSelector({
  value,
  onChange,
  customWidth,
  customHeight,
  onCustomWidthChange,
  onCustomHeightChange,
  disabled = false,
}: AspectRatioSelectorProps): JSX.Element {
  const id = useId();

  return (
    <div className="mb-4">
      <label htmlFor={id} className="mb-1 block text-sm font-medium text-slate-700">
        Aspect ratio
      </label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value as AspectRatio)}
        disabled={disabled}
        className="block w-full rounded border border-surface-border bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-1 disabled:cursor-not-allowed disabled:bg-surface-muted"
      >
        {PRESETS.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
        <option value="custom">custom</option>
      </select>
      <p className="mt-1 text-xs text-slate-500">
        Controls the display container, not the underlying image file.
      </p>

      {value === "custom" ? (
        <div className="mt-3 grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">
              Width
            </label>
            <input
              type="number"
              min={1}
              value={customWidth}
              onChange={(e) => onCustomWidthChange(Number(e.target.value) || 1)}
              disabled={disabled}
              className="block w-full rounded border border-surface-border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">
              Height
            </label>
            <input
              type="number"
              min={1}
              value={customHeight}
              onChange={(e) => onCustomHeightChange(Number(e.target.value) || 1)}
              disabled={disabled}
              className="block w-full rounded border border-surface-border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}