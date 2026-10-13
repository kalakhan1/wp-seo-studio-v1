import { useCallback, useEffect, useState } from "react";
import { Image as ImageIcon, Plus, Search } from "lucide-react";
import { toast } from "sonner";

import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingPage } from "@/components/feedback/Loading";
import { MediaUploader } from "@/components/media/MediaUploader";
import { MediaCard } from "@/components/media/MediaCard";
import { MediaDetailPanel } from "@/components/media/MediaDetailPanel";
import { connectionApi } from "@/services/connectionApi";
import { mediaApi } from "@/services/mediaApi";
import type { Connection } from "@/types/connection";
import type { MediaItem } from "@/types/media";
import { ApiError } from "@/types/errors";

export function MediaStudioPage(): JSX.Element {
  const [connections, setConnections] = useState<Connection[] | null>(null);
  const [activeConnectionId, setActiveConnectionId] = useState<number | null>(
    null,
  );
  const [items, setItems] = useState<MediaItem[] | null>(null);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<MediaItem | null>(null);
  const [showUploader, setShowUploader] = useState(false);

  // Load connections once
  useEffect(() => {
    void (async () => {
      try {
        const res = await connectionApi.list();
        setConnections(res.connections);
        if (res.connections.length > 0 && res.connections[0]) {
          setActiveConnectionId(res.connections[0].id);
        }
      } catch (err) {
        if (err instanceof ApiError) {
          toast.error(`Failed to load connections: ${err.message}`);
        } else {
          toast.error("Failed to load connections.");
        }
        setConnections([]);
      }
    })();
  }, []);

  const reload = useCallback(async () => {
    if (activeConnectionId === null) return;
    try {
      const res = await mediaApi.list({
        connectionId: activeConnectionId,
        query: query || undefined,
        limit: 100,
      });
      setItems(res.items);
      setTotal(res.total);
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Failed to load media: ${err.message}`);
      } else {
        toast.error("Failed to load media.");
      }
      setItems([]);
      setTotal(0);
    }
  }, [activeConnectionId, query]);

  useEffect(() => {
    if (activeConnectionId !== null) {
      void reload();
    }
  }, [activeConnectionId, reload]);

  // --- No connections state ----------------------------------------------

  if (connections !== null && connections.length === 0) {
    return (
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-6 text-2xl font-semibold text-slate-800">
          Media Studio
        </h1>
        <EmptyState
          title="Add a connection first"
          description="Media Studio needs a WordPress connection to upload and manage media."
          icon={<ImageIcon className="h-10 w-10" />}
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

  if (connections === null) {
    return <LoadingPage label="Loading…" />;
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-slate-800">Media Studio</h1>
        <div className="flex items-center gap-2">
          {connections.length > 1 ? (
            <select
              value={activeConnectionId ?? ""}
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
          <button
            type="button"
            onClick={() => setShowUploader((v) => !v)}
            className="inline-flex items-center gap-2 rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
          >
            <Plus className="h-4 w-4" />
            {showUploader ? "Hide uploader" : "Upload media"}
          </button>
        </div>
      </div>

      {showUploader && activeConnectionId !== null ? (
        <MediaUploader
          connectionId={activeConnectionId}
          onUploaded={() => {
            void reload();
          }}
        />
      ) : null}

      <div className="flex items-center gap-2 rounded-lg border border-surface-border bg-white px-3 py-2">
        <Search className="h-4 w-4 text-slate-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by filename…"
          className="w-full bg-transparent text-sm outline-none"
        />
        <span className="text-xs text-slate-500">{total} item(s)</span>
      </div>

      {items === null ? (
        <LoadingPage label="Loading media…" />
      ) : items.length === 0 ? (
        <EmptyState
          title="No media yet"
          description="Upload your first image to reuse it in products, posts, and pages."
          icon={<ImageIcon className="h-10 w-10" />}
          action={
            <button
              type="button"
              onClick={() => setShowUploader(true)}
              className="rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
            >
              Upload media
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
          {items.map((item) => (
            <MediaCard key={item.id} item={item} onSelect={setSelected} />
          ))}
        </div>
      )}

      <MediaDetailPanel
        item={selected}
        onClose={() => setSelected(null)}
        onUpdated={() => void reload()}
      />
    </div>
  );
}