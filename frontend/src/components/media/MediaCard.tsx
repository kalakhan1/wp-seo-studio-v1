import { Image as ImageIcon } from "lucide-react";

import type { MediaItem } from "@/types/media";

interface MediaCardProps {
  item: MediaItem;
  onSelect: (item: MediaItem) => void;
}

function formatBytes(bytes: number | null): string {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function MediaCard({ item, onSelect }: MediaCardProps): JSX.Element {
  return (
    <button
      type="button"
      onClick={() => onSelect(item)}
      className="group flex flex-col overflow-hidden rounded-lg border border-surface-border bg-white text-left transition-shadow hover:shadow-md"
    >
      <div className="relative flex aspect-square items-center justify-center bg-surface-muted">
        {item.url ? (
          <img
            src={item.url}
            alt={item.alt_text || item.filename}
            className="h-full w-full object-cover"
            loading="lazy"
          />
        ) : (
          <ImageIcon className="h-10 w-10 text-slate-300" />
        )}
      </div>
      <div className="flex flex-1 flex-col p-3">
        <p
          className="truncate text-sm font-medium text-slate-800"
          title={item.filename}
        >
          {item.filename}
        </p>
        <p className="mt-0.5 truncate text-xs text-slate-500">
          {item.width && item.height ? `${item.width}×${item.height}` : "—"} ·{" "}
          {formatBytes(item.size_bytes)}
        </p>
      </div>
    </button>
  );
}