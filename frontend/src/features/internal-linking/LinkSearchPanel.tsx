import { useState } from "react";
import { Loader2, Search } from "lucide-react";
import { toast } from "sonner";

import { internalLinkApi } from "@/services/internalLinkApi";
import type { SearchResultItem } from "@/types/internalLink";
import { ApiError } from "@/types/errors";

interface LinkSearchPanelProps {
  connectionId: number;
  onPick: (item: SearchResultItem) => void;
}

export function LinkSearchPanel({
  connectionId,
  onPick,
}: LinkSearchPanelProps): JSX.Element {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResultItem[] | null>(null);
  const [loading, setLoading] = useState(false);

  const doSearch = async (): Promise<void> => {
    const q = query.trim();
    if (!q) return;
    setLoading(true);
    try {
      const res = await internalLinkApi.search(connectionId, q);
      setResults(res.items);
      if (res.warnings.length > 0) {
        res.warnings.forEach((w) => toast.warning(w));
      }
    } catch (err) {
      setResults([]);
      if (err instanceof ApiError) {
        toast.error(`Search failed: ${err.message}`);
      } else {
        toast.error("Search failed.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-lg border border-surface-border bg-white p-5">
      <h2 className="mb-3 text-base font-semibold text-slate-800">
        Search existing content
      </h2>
      <div className="mb-3 flex gap-2">
        <div className="flex flex-1 items-center gap-2 rounded border border-surface-border px-3">
          <Search className="h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                void doSearch();
              }
            }}
            placeholder="Example: badam, hair oil, wellness"
            className="w-full bg-transparent py-2 text-sm outline-none"
          />
        </div>
        <button
          type="button"
          onClick={() => void doSearch()}
          disabled={loading || !query.trim()}
          className="rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            "Search"
          )}
        </button>
      </div>

      {results === null ? null : results.length === 0 ? (
        <p className="text-xs text-slate-500">No matches found.</p>
      ) : (
        <ul className="divide-y divide-surface-border rounded border border-surface-border">
          {results.map((item) => (
            <li
              key={`${item.type}-${item.id}`}
              className="flex items-center gap-3 px-3 py-2 text-sm"
            >
              <span className="inline-flex shrink-0 items-center rounded-full bg-surface-muted px-2 py-0.5 text-xs font-medium text-slate-600">
                {item.type || "item"}
              </span>
              <div className="flex-1 truncate">
                <p className="truncate font-medium text-slate-800">
                  {item.title || "(untitled)"}
                </p>
                <p className="truncate font-mono text-xs text-slate-500">
                  {item.url}
                </p>
              </div>
              <button
                type="button"
                onClick={() => onPick(item)}
                className="rounded border border-brand px-3 py-1 text-xs font-medium text-brand hover:bg-brand-light"
              >
                Add as link
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}