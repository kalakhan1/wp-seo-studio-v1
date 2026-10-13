import { useCallback, useEffect, useState } from "react";
import { Link as LinkIcon, Package, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingPage } from "@/components/feedback/Loading";
import { TextField } from "@/components/inputs/TextField";
import { LinkList, type DraftLink } from "@/features/internal-linking/LinkList";
import { LinkSearchPanel } from "@/features/internal-linking/LinkSearchPanel";
import { connectionApi } from "@/services/connectionApi";
import { internalLinkApi } from "@/services/internalLinkApi";
import type { Connection } from "@/types/connection";
import type {
  SearchResultItem,
  SuggestedLink,
} from "@/types/internalLink";
import { ApiError } from "@/types/errors";

function newId(): string {
  return `link-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function InternalLinkingPage(): JSX.Element {
  const [connections, setConnections] = useState<Connection[] | null>(null);
  const [activeConnectionId, setActiveConnectionId] = useState<number | null>(
    null,
  );
  const [sourceTitle, setSourceTitle] = useState("");
  const [sourceContent, setSourceContent] = useState("");
  const [links, setLinks] = useState<DraftLink[]>([]);
  const [suggestions, setSuggestions] = useState<SuggestedLink[]>([]);
  const [suggesting, setSuggesting] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        const res = await connectionApi.list();
        setConnections(res.connections);
        const first = res.connections[0];
        if (first) setActiveConnectionId(first.id);
      } catch {
        toast.error("Failed to load connections.");
        setConnections([]);
      }
    })();
  }, []);

  // Validate a link URL against the site
  const validateLink = useCallback(
    async (link: DraftLink): Promise<DraftLink> => {
      if (!activeConnectionId) return link;
      if (!link.url) return link;
      try {
        const res = await internalLinkApi.validateUrl(
          activeConnectionId,
          link.url,
        );
        if (!res.ok) {
          return { ...link, warnings: [res.reason] };
        }
      } catch {
        // ignore; keep link as-is
      }
      // Anchor check
      try {
        const existing = links
          .filter((l) => l.id !== link.id)
          .map((l) => l.anchor);
        const res = await internalLinkApi.checkAnchor(link.anchor, existing);
        return { ...link, warnings: res.warnings };
      } catch {
        return link;
      }
    },
    [activeConnectionId, links],
  );

  const addLinkFromSearch = async (item: SearchResultItem): Promise<void> => {
    const draft: DraftLink = {
      id: newId(),
      url: item.url,
      anchor: item.title || item.slug || "Read more",
      linkType: "contextual",
      label: "",
      contextNote: "",
      warnings: [],
    };
    const validated = await validateLink(draft);
    setLinks((prev) => [...prev, validated]);
  };

  const addLinkFromSuggestion = async (s: SuggestedLink): Promise<void> => {
    const draft: DraftLink = {
      id: newId(),
      url: s.url,
      anchor: s.suggested_anchor || s.title,
      linkType: "related_article",
      label: "",
      contextNote: `suggested (score ${s.score})`,
      warnings: [],
    };
    const validated = await validateLink(draft);
    setLinks((prev) => [...prev, validated]);
  };

  const runSuggestions = async (): Promise<void> => {
    if (!activeConnectionId || !sourceTitle.trim()) {
      toast.error("Enter a source title first.");
      return;
    }
    setSuggesting(true);
    try {
      const res = await internalLinkApi.suggest(activeConnectionId, sourceTitle, {
        sourceContent: sourceContent || undefined,
        limit: 8,
      });
      setSuggestions(res.items);
      if (res.items.length === 0) {
        toast.info("No related content was found.");
      }
      if (res.warnings.length > 0) {
        res.warnings.forEach((w) => toast.warning(w));
      }
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Suggestion failed: ${err.message}`);
      } else {
        toast.error("Suggestion failed.");
      }
    } finally {
      setSuggesting(false);
    }
  };

  const handleLinksChanged = (next: DraftLink[]): void => {
    setLinks(next);
    // Re-validate links that changed URLs
    for (const link of next) {
      const prev = links.find((l) => l.id === link.id);
      if (prev && prev.url !== link.url) {
        void validateLink(link).then((updated) => {
          setLinks((cur) =>
            cur.map((l) => (l.id === updated.id ? updated : l)),
          );
        });
      }
    }
  };

  if (connections === null) {
    return <LoadingPage label="Loading…" />;
  }

  if (connections.length === 0) {
    return (
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-6 text-2xl font-semibold text-slate-800">
          Internal Linking Studio
        </h1>
        <EmptyState
          title="Add a connection first"
          description="Internal linking requires a WordPress connection."
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
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold text-slate-800">
            <LinkIcon className="h-6 w-6 text-slate-400" />
            Internal Linking Studio
          </h1>
          <p className="text-sm text-slate-500">
            Prepare internal links for a post or product. Nothing is written
            to WordPress from this page — copy your links into the publisher.
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

      {/* Source context */}
      <section className="rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-3 text-base font-semibold text-slate-800">
          Your content
        </h2>
        <TextField
          label="Source title"
          value={sourceTitle}
          onChange={setSourceTitle}
          placeholder="Example: Badam Benefits Guide"
          help="Used to suggest related content."
        />
        <TextField
          label="Source content (optional)"
          value={sourceContent}
          onChange={setSourceContent}
          placeholder="Paste a short excerpt to improve suggestions."
          help="Not sent anywhere else. Only used for the similarity check."
        />

        <div className="flex justify-end">
          <button
            type="button"
            onClick={() => void runSuggestions()}
            disabled={suggesting || !sourceTitle.trim()}
            className="inline-flex items-center gap-1.5 rounded border border-brand px-3 py-1.5 text-sm font-medium text-brand hover:bg-brand-light disabled:opacity-50"
          >
            <Sparkles className="h-4 w-4" />
            {suggesting ? "Finding related…" : "Suggest related content"}
          </button>
        </div>
      </section>

      {/* Suggestions */}
      {suggestions.length > 0 ? (
        <section className="rounded-lg border border-surface-border bg-white p-5">
          <h2 className="mb-3 text-base font-semibold text-slate-800">
            Suggestions
          </h2>
          <p className="mb-3 text-xs text-slate-500">
            Advisory only. Review before adding. Suggestion is based on title,
            content, and category overlap.
          </p>
          <ul className="divide-y divide-surface-border rounded border border-surface-border">
            {suggestions.map((s) => (
              <li
                key={`${s.target_type}-${s.target_id}`}
                className="flex items-center gap-3 px-3 py-2 text-sm"
              >
                <span className="inline-flex shrink-0 items-center rounded-full bg-surface-muted px-2 py-0.5 text-xs font-medium text-slate-600">
                  {s.target_type}
                </span>
                <div className="flex-1 truncate">
                  <p className="truncate font-medium text-slate-800">
                    {s.title}
                  </p>
                  <p className="text-xs text-slate-500">
                    score {s.score.toFixed(2)}
                    {s.reason ? ` · ${s.reason}` : ""}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => void addLinkFromSuggestion(s)}
                  className="rounded border border-brand px-3 py-1 text-xs font-medium text-brand hover:bg-brand-light"
                >
                  Add
                </button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {/* Search */}
      {activeConnectionId !== null ? (
        <LinkSearchPanel
          connectionId={activeConnectionId}
          onPick={(item) => void addLinkFromSearch(item)}
        />
      ) : null}

      {/* Links list */}
      <section>
        <h2 className="mb-3 text-base font-semibold text-slate-800">
          Your links ({links.length})
        </h2>
        <LinkList links={links} onChange={handleLinksChanged} />
      </section>
    </div>
  );
}