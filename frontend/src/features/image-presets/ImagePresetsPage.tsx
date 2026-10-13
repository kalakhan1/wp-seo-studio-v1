import { useCallback, useEffect, useState } from "react";
import { Copy, Package } from "lucide-react";
import { toast } from "sonner";

import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingPage } from "@/components/feedback/Loading";
import { SelectField } from "@/components/inputs/SelectField";
import { TextField } from "@/components/inputs/TextField";
import { ArchiveGridPreview } from "@/features/image-presets/ArchiveGridPreview";
import { AspectRatioSelector } from "@/features/image-presets/AspectRatioSelector";
import { CSSPresetSelector } from "@/features/image-presets/CSSPresetSelector";
import { DiscoveredSizesTable } from "@/features/image-presets/DiscoveredSizesTable";
import { connectionApi } from "@/services/connectionApi";
import { imagePresetsApi } from "@/services/imagePresetsApi";
import { mediaApi } from "@/services/mediaApi";
import type { Connection } from "@/types/connection";
import type {
  AspectRatio,
  CSSPreset,
  DiscoveredSizesResponse,
  ObjectFit,
  ObjectPosition,
  PresetsResponse,
} from "@/types/imagePresets";
import { ApiError } from "@/types/errors";

const OBJECT_FIT_OPTIONS = [
  { value: "cover", label: "cover" },
  { value: "contain", label: "contain" },
  { value: "fill", label: "fill" },
  { value: "none", label: "none" },
  { value: "scale-down", label: "scale-down" },
];

const OBJECT_POSITION_OPTIONS = [
  { value: "center", label: "center" },
  { value: "top", label: "top" },
  { value: "bottom", label: "bottom" },
  { value: "left", label: "left" },
  { value: "right", label: "right" },
];

export function ImagePresetsPage(): JSX.Element {
  const [connections, setConnections] = useState<Connection[] | null>(null);
  const [activeConnectionId, setActiveConnectionId] = useState<number | null>(
    null,
  );
  const [presets, setPresets] = useState<PresetsResponse | null>(null);
  const [selectedCssKey, setSelectedCssKey] = useState<string | null>(null);

  // Design state
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>("1:1");
  const [customWidth, setCustomWidth] = useState<number>(600);
  const [customHeight, setCustomHeight] = useState<number>(600);
  const [objectFit, setObjectFit] = useState<ObjectFit>("cover");
  const [objectPosition, setObjectPosition] = useState<ObjectPosition>("center");
  const [borderRadius, setBorderRadius] = useState<string>("0");
  const [background, setBackground] = useState<string>("#f8fafc");

  const [discovered, setDiscovered] = useState<DiscoveredSizesResponse | null>(
    null,
  );
  const [discovering, setDiscovering] = useState(false);
  const [sampleImages, setSampleImages] = useState<string[]>([]);

  // Load connections
  useEffect(() => {
    void (async () => {
      try {
        const res = await connectionApi.list();
        setConnections(res.connections);
        const withWc = res.connections.find((c) => c.has_wc_credentials);
        const first = withWc ?? res.connections[0];
        if (first) setActiveConnectionId(first.id);
      } catch {
        toast.error("Failed to load connections.");
        setConnections([]);
      }
    })();
  }, []);

  // Load presets
  useEffect(() => {
    void (async () => {
      try {
        const res = await imagePresetsApi.listPresets();
        setPresets(res);
      } catch {
        toast.error("Failed to load presets.");
      }
    })();
  }, []);

  // Load sample images from media library for the preview
  useEffect(() => {
    if (activeConnectionId === null) return;
    void (async () => {
      try {
        const res = await mediaApi.list({
          connectionId: activeConnectionId,
          limit: 12,
        });
        setSampleImages(
          res.items.map((m) => m.url).filter((u): u is string => Boolean(u)),
        );
      } catch {
        setSampleImages([]);
      }
    })();
  }, [activeConnectionId]);

  const applyCSSPreset = useCallback((preset: CSSPreset) => {
    setSelectedCssKey(preset.key);
    setAspectRatio(preset.aspect_ratio);
    setObjectFit(preset.object_fit);
    setObjectPosition(preset.object_position);
    setBorderRadius(preset.border_radius);
    setBackground(preset.background);
  }, []);

  const discover = useCallback(async () => {
    if (activeConnectionId === null) return;
    setDiscovering(true);
    try {
      const res = await imagePresetsApi.discoverSizes(activeConnectionId);
      setDiscovered(res);
    } catch (err) {
      setDiscovered(null);
      if (err instanceof ApiError) {
        toast.error(`Discovery failed: ${err.message}`);
      } else {
        toast.error("Discovery failed.");
      }
    } finally {
      setDiscovering(false);
    }
  }, [activeConnectionId]);

  const copyCss = useCallback(async () => {
    const aspect = aspectRatio === "custom"
      ? `${customWidth} / ${customHeight}`
      : aspectRatio.replace(":", " / ");
    const css = `.wc-product-card__image {
  width: 100%;
  aspect-ratio: ${aspect};
  background-color: ${background};
  border-radius: ${borderRadius};
  overflow: hidden;
}

.wc-product-card__image img {
  width: 100%;
  height: 100%;
  object-fit: ${objectFit};
  object-position: ${objectPosition};
  display: block;
}`;
    try {
      await navigator.clipboard.writeText(css);
      toast.success("CSS copied to clipboard.");
    } catch {
      toast.error("Could not copy CSS. Select and copy manually.");
    }
  }, [
    aspectRatio,
    customWidth,
    customHeight,
    objectFit,
    objectPosition,
    background,
    borderRadius,
  ]);

  if (connections === null || presets === null) {
    return <LoadingPage label="Loading…" />;
  }

  if (connections.length === 0) {
    return (
      <div className="mx-auto max-w-5xl">
        <h1 className="mb-6 text-2xl font-semibold text-slate-800">
          Image Presets
        </h1>
        <EmptyState
          title="Add a connection first"
          description="Image preset discovery uses a WordPress connection to list registered sizes."
          icon={<Package className="h-10 w-10" />}
          action={
            <a
              href="/connection"
              className="rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
            >
              Go to Website Connection
            </a>
          }
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-800">
            Image Presets
          </h1>
          <p className="text-sm text-slate-500">
            Design a balanced archive grid. Preview it before applying any
            CSS to your theme.
          </p>
        </div>
        {connections.length > 1 ? (
          <select
            value={activeConnectionId?.toString() ?? ""}
            onChange={(e) => setActiveConnectionId(Number(e.target.value))}
            className="rounded border border-surface-border bg-white px-3 py-2 text-sm"
          >
            {connections.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
        ) : null}
      </div>

      {/* CSS presets */}
      <section className="rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-3 text-base font-semibold text-slate-800">
          CSS display presets
        </h2>
        <CSSPresetSelector
          presets={presets.css}
          selectedKey={selectedCssKey}
          onSelect={applyCSSPreset}
        />
      </section>

      {/* Fine-grained controls */}
      <section className="rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-4 text-base font-semibold text-slate-800">
          Fine controls
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <AspectRatioSelector
            value={aspectRatio}
            onChange={setAspectRatio}
            customWidth={customWidth}
            customHeight={customHeight}
            onCustomWidthChange={setCustomWidth}
            onCustomHeightChange={setCustomHeight}
          />

          <div>
            <SelectField
              label="object-fit"
              value={objectFit}
              onChange={(v) => setObjectFit(v as ObjectFit)}
              options={OBJECT_FIT_OPTIONS}
              help="cover fills the container; contain shows the entire image."
            />

            <SelectField
              label="object-position"
              value={objectPosition}
              onChange={(v) => setObjectPosition(v as ObjectPosition)}
              options={OBJECT_POSITION_OPTIONS}
              help="Where the image is anchored inside the container."
            />

            <TextField
              label="Border radius"
              value={borderRadius}
              onChange={setBorderRadius}
              placeholder="Example: 12px"
              help="CSS length. Use 0 for sharp corners."
            />

            <TextField
              label="Background color"
              value={background}
              onChange={setBackground}
              placeholder="Example: #f8fafc"
              help="Shown behind transparent images."
            />
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <button
            type="button"
            onClick={() => void copyCss()}
            className="inline-flex items-center gap-2 rounded border border-brand px-4 py-2 text-sm font-medium text-brand hover:bg-brand-light"
          >
            <Copy className="h-4 w-4" />
            Copy CSS
          </button>
        </div>
      </section>

      {/* Preview */}
      <ArchiveGridPreview
        aspectRatio={aspectRatio}
        customWidth={customWidth}
        customHeight={customHeight}
        objectFit={objectFit}
        objectPosition={objectPosition}
        borderRadius={borderRadius}
        background={background}
        sampleImages={sampleImages}
      />

      {/* Suggested presets reference */}
      <section className="rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-3 text-base font-semibold text-slate-800">
          Suggested presets
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-border text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-3">Key</th>
                <th className="py-2 pr-3">Label</th>
                <th className="py-2 pr-3">Dimensions</th>
                <th className="py-2 pr-3">Aspect</th>
                <th className="py-2 pr-3">Description</th>
              </tr>
            </thead>
            <tbody>
              {presets.suggested.map((p) => (
                <tr key={p.key} className="border-b border-surface-border/60">
                  <td className="py-2 pr-3 font-mono text-slate-800">
                    {p.key}
                  </td>
                  <td className="py-2 pr-3 text-slate-800">{p.label}</td>
                  <td className="py-2 pr-3 font-mono text-slate-700">
                    {p.width} × {p.height}
                  </td>
                  <td className="py-2 pr-3 font-mono text-slate-700">
                    {p.aspect_ratio}
                  </td>
                  <td className="py-2 pr-3 text-xs text-slate-500">
                    {p.description}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Discovered sizes */}
      <DiscoveredSizesTable
        data={discovered}
        loading={discovering}
        onRefresh={() => void discover()}
      />
    </div>
  );
}