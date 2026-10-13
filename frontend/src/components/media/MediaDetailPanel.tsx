import { useEffect, useState } from "react";
import { Trash2, X } from "lucide-react";
import { toast } from "sonner";

import { TextField } from "@/components/inputs/TextField";
import { TextArea } from "@/components/inputs/TextArea";
import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { mediaApi } from "@/services/mediaApi";
import type { MediaItem } from "@/types/media";
import { ApiError } from "@/types/errors";

interface MediaDetailPanelProps {
  item: MediaItem | null;
  onClose: () => void;
  onUpdated: () => void;
}

export function MediaDetailPanel({
  item,
  onClose,
  onUpdated,
}: MediaDetailPanelProps): JSX.Element | null {
  const [title, setTitle] = useState("");
  const [altText, setAltText] = useState("");
  const [caption, setCaption] = useState("");
  const [description, setDescription] = useState("");
  const [sync, setSync] = useState(true);
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    if (!item) return;
    setTitle(item.title ?? "");
    setAltText(item.alt_text ?? "");
    setCaption(item.caption ?? "");
    setDescription(item.description ?? "");
    setSync(true);
  }, [item]);

  if (!item) return null;

  const dirty =
    title !== (item.title ?? "") ||
    altText !== (item.alt_text ?? "") ||
    caption !== (item.caption ?? "") ||
    description !== (item.description ?? "");

  const handleSave = async (): Promise<void> => {
    setSaving(true);
    try {
      await mediaApi.update(item.id, {
        title,
        alt_text: altText,
        caption,
        description,
        sync_to_wordpress: sync,
      });
      toast.success("Media updated.");
      onUpdated();
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Save failed: ${err.message}`);
      } else {
        toast.error("Save failed.");
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (): Promise<void> => {
    setConfirmDelete(false);
    try {
      await mediaApi.remove(item.id, false);
      toast.success("Media moved to trash.");
      onClose();
      onUpdated();
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Delete failed: ${err.message}`);
      } else {
        toast.error("Delete failed.");
      }
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-slate-900/40"
      onClick={onClose}
    >
      <div
        className="h-full w-full max-w-xl overflow-y-auto bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-surface-border bg-white px-5 py-3">
          <h2 className="text-base font-semibold text-slate-800">
            Media details
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-slate-500 hover:bg-surface-muted"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        <div className="p-5">
          {item.url ? (
            <div className="mb-4 overflow-hidden rounded-lg border border-surface-border bg-surface-muted">
              <img
                src={item.url}
                alt={item.alt_text || item.filename}
                className="mx-auto max-h-80 object-contain"
              />
            </div>
          ) : null}

          <dl className="mb-6 grid grid-cols-2 gap-3 text-xs">
            <div>
              <dt className="text-slate-500">Filename</dt>
              <dd className="truncate font-mono text-slate-800">
                {item.filename}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">WordPress ID</dt>
              <dd className="font-mono text-slate-800">
                {item.wp_media_id ?? "—"}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">MIME</dt>
              <dd className="font-mono text-slate-800">{item.mime ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Dimensions</dt>
              <dd className="font-mono text-slate-800">
                {item.width && item.height
                  ? `${item.width} × ${item.height}`
                  : "—"}
              </dd>
            </div>
          </dl>

          <TextField
            label="Title"
            value={title}
            onChange={setTitle}
            placeholder="Example: Herbal Hair Oil"
          />
          <TextField
            label="Alt text"
            value={altText}
            onChange={setAltText}
            placeholder="Example: Bottle of herbal hair oil on a wooden table"
            help="Important for accessibility and SEO."
            maxLength={125}
            showCounter
          />
          <TextField
            label="Caption"
            value={caption}
            onChange={setCaption}
            placeholder="Example: Our best-selling hair oil."
          />
          <TextArea
            label="Description"
            value={description}
            onChange={setDescription}
            placeholder="Example: 100ml amber glass bottle with dropper cap."
            rows={3}
          />

          <label className="mb-4 flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={sync}
              onChange={(e) => setSync(e.target.checked)}
              className="h-4 w-4 rounded border-surface-border"
            />
            Sync changes to WordPress
          </label>

          <div className="flex justify-between gap-2 border-t border-surface-border pt-4">
            <button
              type="button"
              onClick={() => setConfirmDelete(true)}
              className="inline-flex items-center gap-1 rounded border border-danger px-3 py-2 text-sm font-medium text-danger hover:bg-danger-light"
            >
              <Trash2 className="h-4 w-4" />
              Delete
            </button>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded border border-surface-border px-4 py-2 text-sm font-medium text-slate-700 hover:bg-surface-muted"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => void handleSave()}
                disabled={saving || !dirty}
                className="rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
              >
                {saving ? "Saving…" : "Save"}
              </button>
            </div>
          </div>
        </div>

        <ConfirmDialog
          open={confirmDelete}
          title={`Delete "${item.filename}"?`}
          description="The media will be moved to the WordPress trash and removed from the local cache. This can't be undone from here."
          confirmLabel="Delete"
          variant="danger"
          onConfirm={() => void handleDelete()}
          onCancel={() => setConfirmDelete(false)}
        />
      </div>
    </div>
  );
}