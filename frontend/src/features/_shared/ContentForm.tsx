import { useEffect, useState } from "react";
import { Save, Send, Calendar, RotateCcw } from "lucide-react";
import { toast } from "sonner";

import { RankMathFields } from "@/features/_shared/RankMathFields";
import { TextField } from "@/components/inputs/TextField";
import { TextArea } from "@/components/inputs/TextArea";
import { SelectField } from "@/components/inputs/SelectField";
import { contentApi, taxonomyApi } from "@/services/contentApi";
import { connectionApi } from "@/services/connectionApi";
import type {
  CategoryItem,
  ContentKind,
  ContentPublishResponse,
  ContentStatus,
  RankMathMeta,
  TagItem,
} from "@/types/content";
import type { Connection } from "@/types/connection";
import { ApiError } from "@/types/errors";

interface ContentFormProps {
  kind: ContentKind;
}

interface FormState {
  connectionId: number | null;
  title: string;
  slug: string;
  content: string;
  excerpt: string;
  status: ContentStatus;
  scheduledDate: string;
  featuredMediaId: string;
  categoryIds: number[];
  tagIds: number[];
  parentId: string;
  menuOrder: number;
  commentStatus: "open" | "closed";
  pingStatus: "open" | "closed";
  rankMath: RankMathMeta;
}

const INITIAL: FormState = {
  connectionId: null,
  title: "",
  slug: "",
  content: "",
  excerpt: "",
  status: "draft",
  scheduledDate: "",
  featuredMediaId: "",
  categoryIds: [],
  tagIds: [],
  parentId: "",
  menuOrder: 0,
  commentStatus: "open",
  pingStatus: "open",
  rankMath: {},
};

const STATUS_OPTIONS = [
  { value: "draft", label: "Draft" },
  { value: "publish", label: "Publish" },
  { value: "future", label: "Schedule" },
  { value: "pending", label: "Pending review" },
  { value: "private", label: "Private" },
];

export function ContentForm({ kind }: ContentFormProps): JSX.Element {
  const isPost = kind === "post";
  const [connections, setConnections] = useState<Connection[]>([]);
  const [form, setForm] = useState<FormState>(INITIAL);
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [tags, setTags] = useState<TagItem[]>([]);
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState<ContentPublishResponse | null>(null);

  // Load connections
  useEffect(() => {
    void (async () => {
      try {
        const res = await connectionApi.list();
        setConnections(res.connections);
        const first = res.connections[0];
        if (first) {
          setForm((f) => ({ ...f, connectionId: first.id }));
        }
      } catch {
        toast.error("Failed to load connections.");
      }
    })();
  }, []);

  // Load categories + tags when connection changes (posts only)
  useEffect(() => {
    if (!isPost || !form.connectionId) return;
    void (async () => {
      try {
        const [cats, tgs] = await Promise.all([
          taxonomyApi.listCategories(form.connectionId as number),
          taxonomyApi.listTags(form.connectionId as number),
        ]);
        setCategories(cats.items);
        setTags(tgs.items);
      } catch {
        // Silent: user may not have categories yet.
        setCategories([]);
        setTags([]);
      }
    })();
  }, [isPost, form.connectionId]);

  const update = <K extends keyof FormState>(key: K, value: FormState[K]): void => {
    setForm((f) => ({ ...f, [key]: value }));
  };

  const updateRankMath = (next: RankMathMeta): void => {
    setForm((f) => ({ ...f, rankMath: next }));
  };

  const reset = (): void => {
    setForm({
      ...INITIAL,
      connectionId: form.connectionId,
    });
    setResult(null);
  };

  const validate = (): string | null => {
    if (!form.connectionId) return "Select a connection.";
    if (!form.title.trim()) return "Title is required.";
    if (form.status === "future" && !form.scheduledDate) {
      return "Scheduled date is required for scheduled posts.";
    }
    return null;
  };

  const submit = async (statusOverride?: ContentStatus): Promise<void> => {
    const status = statusOverride ?? form.status;
    if (status !== form.status) {
      update("status", status);
    }
    const error = validate();
    if (error) {
      toast.error(error);
      return;
    }
    setSaving(true);
    setResult(null);
    try {
      const payload = {
        connection_id: form.connectionId as number,
        kind,
        title: form.title.trim(),
        slug: form.slug.trim() || undefined,
        content: form.content,
        excerpt: form.excerpt,
        status,
        scheduled_date: form.scheduledDate || undefined,
        featured_media_id: form.featuredMediaId
          ? Number(form.featuredMediaId)
          : undefined,
        categories: isPost ? form.categoryIds : undefined,
        tags: isPost ? form.tagIds : undefined,
        parent_id:
          !isPost && form.parentId ? Number(form.parentId) : undefined,
        menu_order: form.menuOrder,
        comment_status: form.commentStatus,
        ping_status: form.pingStatus,
        rank_math:
          Object.keys(form.rankMath).length > 0 ? form.rankMath : undefined,
      };
      const res = isPost
        ? await contentApi.createPost(payload)
        : await contentApi.createPage(payload);
      setResult(res);
      if (res.partial) {
        toast.warning(`Saved with warnings. ${res.message}`);
      } else {
        toast.success(res.message || "Saved.");
      }
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Failed: ${err.message}`);
      } else {
        toast.error("Failed to save.");
      }
    } finally {
      setSaving(false);
    }
  };

  const disabled = saving;

  return (
    <div className="space-y-6">
      {/* Actions bar */}
      <div className="flex flex-wrap items-center gap-2 rounded-lg border border-surface-border bg-white px-4 py-3">
        <button
          type="button"
          onClick={() => void submit("draft")}
          disabled={disabled}
          className="inline-flex items-center gap-1.5 rounded border border-surface-border px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-surface-muted disabled:opacity-50"
        >
          <Save className="h-4 w-4" />
          Save Draft
        </button>
        <button
          type="button"
          onClick={() => void submit("publish")}
          disabled={disabled}
          className="inline-flex items-center gap-1.5 rounded bg-brand px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
        >
          <Send className="h-4 w-4" />
          Publish
        </button>
        <button
          type="button"
          onClick={() => void submit("future")}
          disabled={disabled}
          className="inline-flex items-center gap-1.5 rounded border border-brand px-3 py-1.5 text-sm font-medium text-brand hover:bg-brand-light disabled:opacity-50"
        >
          <Calendar className="h-4 w-4" />
          Schedule
        </button>
        <button
          type="button"
          onClick={reset}
          disabled={disabled}
          className="ml-auto inline-flex items-center gap-1.5 rounded border border-surface-border px-3 py-1.5 text-sm font-medium text-slate-500 hover:bg-surface-muted disabled:opacity-50"
        >
          <RotateCcw className="h-4 w-4" />
          Reset
        </button>
      </div>

      {/* Basic */}
      <section className="rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-4 text-base font-semibold text-slate-800">
          Basic Information
        </h2>

        {connections.length > 1 ? (
          <SelectField
            label="Connection"
            value={form.connectionId?.toString() ?? ""}
            onChange={(v) => update("connectionId", Number(v))}
            options={connections.map((c) => ({
              value: c.id.toString(),
              label: c.label,
            }))}
            help="Which WordPress site to publish to."
          />
        ) : null}

        <TextField
          label="Title"
          value={form.title}
          onChange={(v) => update("title", v)}
          placeholder={
            isPost
              ? "Example: Badam Benefits Guide"
              : "Example: About Us"
          }
          required
          maxLength={500}
        />

        <TextField
          label="Slug"
          value={form.slug}
          onChange={(v) => update("slug", v)}
          placeholder="Example: badam-benefits-guide"
          help="URL-friendly identifier. Leave empty to let WordPress generate one."
          maxLength={300}
        />

        {isPost ? (
          <TextArea
            label="Excerpt"
            value={form.excerpt}
            onChange={(v) => update("excerpt", v)}
            placeholder="Example: A practical guide to badam."
            help="Shown in blog listings and search previews."
            rows={2}
            maxLength={300}
            showCounter
          />
        ) : null}

        <TextArea
          label="Content (HTML allowed)"
          value={form.content}
          onChange={(v) => update("content", v)}
          placeholder="<p>Your content here.</p>"
          help="HTML is sanitized by WordPress on save."
          rows={12}
        />

        <SelectField
          label="Status"
          value={form.status}
          onChange={(v) => update("status", v as ContentStatus)}
          options={STATUS_OPTIONS}
          help="Use Publish button to override this at submit time."
        />

        {form.status === "future" ? (
          <TextField
            label="Scheduled date & time"
            value={form.scheduledDate}
            onChange={(v) => update("scheduledDate", v)}
            placeholder="Example: 2026-11-01T10:00:00"
            help="ISO 8601 format. WordPress will publish at this time."
            required
          />
        ) : null}
      </section>

      {/* Organization (posts only) */}
      {isPost ? (
        <section className="rounded-lg border border-surface-border bg-white p-5">
          <h2 className="mb-4 text-base font-semibold text-slate-800">
            Organization
          </h2>

          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-slate-700">
              Categories
            </label>
            {categories.length === 0 ? (
              <p className="text-xs text-slate-500">
                No categories yet on this site.
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {categories.map((c) => (
                  <label
                    key={c.id}
                    className={`inline-flex cursor-pointer items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium ${
                      form.categoryIds.includes(c.id)
                        ? "border-brand bg-brand-light text-brand-dark"
                        : "border-surface-border bg-white text-slate-600 hover:bg-surface-muted"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={form.categoryIds.includes(c.id)}
                      onChange={(e) => {
                        const next = e.target.checked
                          ? [...form.categoryIds, c.id]
                          : form.categoryIds.filter((x) => x !== c.id);
                        update("categoryIds", next);
                      }}
                      className="hidden"
                    />
                    {c.name} ({c.count})
                  </label>
                ))}
              </div>
            )}
          </div>

          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-slate-700">
              Tags
            </label>
            {tags.length === 0 ? (
              <p className="text-xs text-slate-500">
                No tags yet on this site.
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {tags.map((t) => (
                  <label
                    key={t.id}
                    className={`inline-flex cursor-pointer items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium ${
                      form.tagIds.includes(t.id)
                        ? "border-brand bg-brand-light text-brand-dark"
                        : "border-surface-border bg-white text-slate-600 hover:bg-surface-muted"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={form.tagIds.includes(t.id)}
                      onChange={(e) => {
                        const next = e.target.checked
                          ? [...form.tagIds, t.id]
                          : form.tagIds.filter((x) => x !== t.id);
                        update("tagIds", next);
                      }}
                      className="hidden"
                    />
                    {t.name} ({t.count})
                  </label>
                ))}
              </div>
            )}
          </div>
        </section>
      ) : (
        <section className="rounded-lg border border-surface-border bg-white p-5">
          <h2 className="mb-4 text-base font-semibold text-slate-800">
            Page Structure
          </h2>

          <TextField
            label="Parent page ID"
            value={form.parentId}
            onChange={(v) => update("parentId", v)}
            placeholder="Example: 12"
            help="Optional. Numeric WordPress page ID."
            type="number"
          />

          <TextField
            label="Menu order"
            value={form.menuOrder.toString()}
            onChange={(v) => update("menuOrder", Number(v) || 0)}
            placeholder="Example: 0"
            help="Lower numbers appear first in menus."
            type="number"
          />
        </section>
      )}

      {/* Advanced */}
      <section className="rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-4 text-base font-semibold text-slate-800">
          Advanced
        </h2>
        <TextField
          label="Featured media ID"
          value={form.featuredMediaId}
          onChange={(v) => update("featuredMediaId", v)}
          placeholder="Example: 101"
          help="Numeric WordPress media ID. Upload first in Media Studio."
          type="number"
        />
        <SelectField
          label="Comment status"
          value={form.commentStatus}
          onChange={(v) => update("commentStatus", v as "open" | "closed")}
          options={[
            { value: "open", label: "Open" },
            { value: "closed", label: "Closed" },
          ]}
        />
        <SelectField
          label="Ping status"
          value={form.pingStatus}
          onChange={(v) => update("pingStatus", v as "open" | "closed")}
          options={[
            { value: "open", label: "Open" },
            { value: "closed", label: "Closed" },
          ]}
        />
      </section>

      {/* Rank Math */}
      <section className="rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-4 text-base font-semibold text-slate-800">
          Rank Math SEO
        </h2>
        <RankMathFields
          value={form.rankMath}
          onChange={updateRankMath}
          disabled={disabled}
        />
      </section>

      {/* Result */}
      {result ? (
        <section
          className={`rounded-lg border p-5 ${
            result.partial
              ? "border-warning bg-warning-light/30"
              : "border-success bg-success-light/30"
          }`}
        >
          <h3 className="mb-2 text-sm font-semibold">
            {result.partial ? "Saved with warnings" : "Saved successfully"}
          </h3>
          <p className="mb-2 text-sm text-slate-700">{result.message}</p>
          {result.permalink ? (
            <p className="text-xs">
              Permalink:{" "}
              <a
                href={result.permalink}
                target="_blank"
                rel="noreferrer"
                className="font-mono text-brand underline"
              >
                {result.permalink}
              </a>
            </p>
          ) : null}
          {result.warnings.length > 0 ? (
            <ul className="mt-2 ml-4 list-disc space-y-0.5 text-xs text-warning">
              {result.warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}