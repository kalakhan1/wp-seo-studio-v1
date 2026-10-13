import { useMemo, useState } from "react";
import { Monitor, Smartphone, Tablet } from "lucide-react";

import type {
  AspectRatio,
  ObjectFit,
  ObjectPosition,
} from "@/types/imagePresets";

interface ArchiveGridPreviewProps {
  aspectRatio: AspectRatio;
  customWidth: number;
  customHeight: number;
  objectFit: ObjectFit;
  objectPosition: ObjectPosition;
  borderRadius: string;
  background: string;
  sampleImages: string[];
}

type Device = "desktop" | "tablet" | "mobile";

const DEVICE_WIDTH: Record<Device, string> = {
  desktop: "100%",
  tablet: "640px",
  mobile: "375px",
};

const DEVICE_COLUMNS: Record<Device, string> = {
  desktop: "repeat(4, minmax(0, 1fr))",
  tablet: "repeat(3, minmax(0, 1fr))",
  mobile: "repeat(2, minmax(0, 1fr))",
};

const SAMPLE_PRODUCT_NAMES = [
  "Herbal Hair Oil",
  "Badam Oil",
  "Natural Face Wash",
  "Herbal Shampoo",
  "Body Lotion with Almonds",
  "Amla Hair Tonic",
  "Neem Soap Bar",
  "Coconut Hair Mask",
];

function computeAspectStyle(
  ratio: AspectRatio,
  cw: number,
  ch: number,
): string {
  if (ratio === "custom") {
    return `${cw} / ${ch}`;
  }
  return ratio.replace(":", " / ");
}

export function ArchiveGridPreview({
  aspectRatio,
  customWidth,
  customHeight,
  objectFit,
  objectPosition,
  borderRadius,
  background,
  sampleImages,
}: ArchiveGridPreviewProps): JSX.Element {
  const [device, setDevice] = useState<Device>("desktop");

  const aspect = useMemo(
    () => computeAspectStyle(aspectRatio, customWidth, customHeight),
    [aspectRatio, customWidth, customHeight],
  );

  const visible = sampleImages.length > 0
    ? sampleImages
    : [""];

  return (
    <div className="rounded-lg border border-surface-border bg-white p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-base font-semibold text-slate-800">
          Archive Grid Preview
        </h2>
        <div className="inline-flex overflow-hidden rounded border border-surface-border">
          {(["desktop", "tablet", "mobile"] as Device[]).map((d) => {
            const Icon =
              d === "desktop"
                ? Monitor
                : d === "tablet"
                  ? Tablet
                  : Smartphone;
            return (
              <button
                key={d}
                type="button"
                onClick={() => setDevice(d)}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium ${
                  device === d
                    ? "bg-brand-light text-brand-dark"
                    : "bg-white text-slate-600 hover:bg-surface-muted"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                <span className="capitalize">{d}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="mx-auto transition-all" style={{ width: DEVICE_WIDTH[device] }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: DEVICE_COLUMNS[device],
            gap: "12px",
          }}
        >
          {SAMPLE_PRODUCT_NAMES.slice(0, 8).map((name, i) => {
            const imgSrc = visible[i % visible.length] ?? "";
            return (
              <div
                key={i}
                className="flex flex-col overflow-hidden rounded-lg border border-surface-border bg-white"
              >
                <div
                  style={{
                    aspectRatio: aspect,
                    backgroundColor: background,
                    borderRadius,
                    overflow: "hidden",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    width: "100%",
                  }}
                >
                  {imgSrc ? (
                    <img
                      src={imgSrc}
                      alt={name}
                      style={{
                        width: "100%",
                        height: "100%",
                        objectFit,
                        objectPosition,
                      }}
                    />
                  ) : (
                    <span className="text-xs text-slate-400">sample</span>
                  )}
                </div>
                <div className="p-2">
                  <p className="line-clamp-2 text-xs font-medium text-slate-800">
                    {name}
                  </p>
                  <p className="mt-0.5 text-xs text-brand-dark">
                    Rs 499.00
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <p className="mt-3 text-xs text-slate-500">
        This is a design preview only. The connected site's theme still
        controls the real archive. Copy the CSS below to apply a similar
        look.
      </p>
    </div>
  );
}