import { useEffect, useState } from "react";
import { Image as ImageIcon, X } from "lucide-react";
import { toast } from "sonner";

import { mediaApi } from "@/services/mediaApi";
import type { MediaItem } from "@/types/media";

interface MediaPickerProps {
  connectionId: number;
  value: MediaItem | null;
  onChange: (item: MediaItem | null) => void;
  label?: string;
  help?: string;
}

/**
 * Simple media picker: opens a modal listing media from the local cache.
 * The user selects one item, which becomes the value.
 *
 * Uploading new media happens in Media Studio; this picker only reuses
 * existing items.
 */
export function MediaPicker({
  connectionId,
  value,
  onChange,
  label = "Featured image",
  help = "Pick an image from your Media Studio library.",
}: MediaPickerProps): JSX.Element {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<MediaItem[] | null>(null);

  useEffect(() => {
    if (!open) return;
    void (async () => {
      try {
        const res = await mediaApi.list({
          connectionId,
          limit: 100,
        });
        setItems(res.items);
      } catch {
        toast.error("Failed to load media library.");
        setItems([]);
      }
    })();
  }, [open, connectionId]);

  return (
    <div className="mb-4">
      <label className="mb-1 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <div className="flex items-start gap-3">
        <div className="flex h-24 w-24 items-center justify-center overflow-hidden rounded border border-surface-border bg-surface-muted">
          {value?.url ? (
            <img
              src={value.url}
              alt={value.alt_text || value.filename}
              className="h-full w-full object-cover"
            />
          ) : (
            <ImageIcon className="h-8 w-8 text-slate-300" />
          )}
        </div>
        <div className="flex flex-1 flex-col gap-2">
          {value ? (
            <>
              <p className="truncate text-sm font-medium text-slate-800">
                {value.filename}
              </p>
              <p className="text-xs text-slate-500">
                WP ID: {value.wp_media_id ?? "—"}
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setOpen(true)}
                  className="rounded border border-surface-border px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-surface-muted"
                >
                  Change
                </button>
                <button
                  type="button"
                  onClick={() => onChange(null)}
                  className="inline-flex items-center gap-1 rounded border border-danger px-3 py-1.5 text-xs font-medium text-danger hover:bg-danger-light"
                >
                  <X className="h-3 w-3" />
                  Remove
                </button>
              </div>
            </>
          ) : (
            <button
              type="button"
              onClick={() => setOpen(true)}
              className="self-start rounded bg-brand px-3 py-2 text-sm font-medium text-white hover:bg-brand-dark"
            >
              Choose from library
            </button>
          )}
          {help ? <p className="text-xs text-slate-500">{help}</p> : null}
        </div>
      </div>

      {open ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
          onClick={() => setOpen(false)}
        >
          <div
            className="max-h-[80vh] w-full max-w-3xl overflow-y-auto rounded-lg bg-white p-5 shadow-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-base font-semibold text-slate-800">
                Media library
              </h3>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="rounded p-1 text-slate-500 hover:bg-surface-muted"
                aria-label="Close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            {items === null ? (
              <p className="py-8 text-center text-sm text-slate-500">
                Loading…
              </p>
            ) : items.length === 0 ? (
              <p className="py-8 text-center text-sm text-slate-500">
                No media yet. Upload images in Media Studio first.
              </p>
            ) : (
              <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-5">
                {items.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => {
                      onChange(item);
                      setOpen(false);
                    }}
                    className="overflow-hidden rounded border border-surface-border text-left hover:shadow-md"
                  >
                    <div className="aspect-square bg-surface-muted">
                      {item.url ? (
                        <img
                          src={item.url}
                          alt={item.alt_text || item.filename}
                          className="h-full w-full object-cover"
                        />
                      ) : (
                        <div className="flex h-full items-center justify-center">
                          <ImageIcon className="h-6 w-6 text-slate-300" />
                        </div>
                      )}
                    </div>
                    <p className="truncate p-1.5 text-xs text-slate-700">
                      {item.filename}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}