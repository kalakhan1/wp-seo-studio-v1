import { useMemo, useState } from "react";
import { Save, RotateCcw } from "lucide-react";
import { toast } from "sonner";

import {
  BooleanToggle,
  SettingsSection,
  TextInput,
} from "@/features/rankmath/SettingsSection";
import { rankmathSettingsApi } from "@/services/rankmathSettingsApi";
import type {
  RankMathSettings,
  RankMathSettingUpdate,
} from "@/types/rankmathSettings";
import { ApiError } from "@/types/errors";

interface RankMathSettingsFormProps {
  connectionId: number;
  settings: RankMathSettings;
  onSaved: (updated: RankMathSettings) => void;
  disabled?: boolean;
}

export function RankMathSettingsForm({
  connectionId,
  settings,
  onSaved,
  disabled = false,
}: RankMathSettingsFormProps): JSX.Element {
  const [draft, setDraft] = useState<RankMathSettings>(settings);
  const [saving, setSaving] = useState(false);

  const dirtyKeys = useMemo(() => {
    const keys: (keyof RankMathSettings)[] = [];
    for (const k of Object.keys(draft) as (keyof RankMathSettings)[]) {
      if (draft[k] !== settings[k]) keys.push(k);
    }
    return keys;
  }, [draft, settings]);

  const update = <K extends keyof RankMathSettings>(
    key: K,
    value: RankMathSettings[K],
  ): void => {
    setDraft((d) => ({ ...d, [key]: value }));
  };

  const reset = (): void => {
    setDraft(settings);
  };

  const handleSave = async (): Promise<void> => {
    if (dirtyKeys.length === 0) return;
    setSaving(true);
    try {
      const payload: RankMathSettingUpdate = {};
      for (const k of dirtyKeys) {
        (payload as Record<string, unknown>)[k] = draft[k];
      }
      const res = await rankmathSettingsApi.updateSettings(
        connectionId,
        payload,
      );
      toast.success(`Updated ${res.changed.length} setting(s).`);
      onSaved(res.settings);
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

  const isDisabled = disabled || saving;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between rounded-lg border border-surface-border bg-white px-4 py-3">
        <p className="text-sm text-slate-600">
          {dirtyKeys.length === 0
            ? "No unsaved changes."
            : `${dirtyKeys.length} unsaved change(s).`}
        </p>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={reset}
            disabled={isDisabled || dirtyKeys.length === 0}
            className="inline-flex items-center gap-1.5 rounded border border-surface-border px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-surface-muted disabled:opacity-50"
          >
            <RotateCcw className="h-4 w-4" />
            Reset
          </button>
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={isDisabled || dirtyKeys.length === 0}
            className="inline-flex items-center gap-1.5 rounded bg-brand px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
          >
            <Save className="h-4 w-4" />
            {saving ? "Saving…" : "Save changes"}
          </button>
        </div>
      </div>

      <SettingsSection
        title="Titles & Meta"
        description="Controls how titles and descriptions appear across the site."
      >
        <TextInput
          label="Title separator"
          value={draft.title_separator}
          onChange={(v) => update("title_separator", v)}
          placeholder="Example: |"
          help="Character between the page title and the site name."
          maxLength={5}
          disabled={isDisabled}
        />
        <TextInput
          label="Homepage SEO title"
          value={draft.homepage_title}
          onChange={(v) => update("homepage_title", v)}
          placeholder="Example: Herbal Care — Natural Products for Daily Use"
          maxLength={500}
          disabled={isDisabled}
        />
        <TextInput
          label="Homepage meta description"
          value={draft.homepage_description}
          onChange={(v) => update("homepage_description", v)}
          placeholder="Example: Natural herbal products for daily care."
          maxLength={500}
          disabled={isDisabled}
        />
      </SettingsSection>

      <SettingsSection
        title="Sitemap"
        description="What gets included in the XML sitemap that search engines read."
      >
        <BooleanToggle
          label="Enable XML sitemap"
          help="Rank Math generates a sitemap at /sitemap_index.xml."
          value={draft.sitemap_enabled}
          onChange={(v) => update("sitemap_enabled", v)}
          disabled={isDisabled}
        />
        <BooleanToggle
          label="Include products"
          value={draft.sitemap_include_products}
          onChange={(v) => update("sitemap_include_products", v)}
          disabled={isDisabled}
        />
        <BooleanToggle
          label="Include blog posts"
          value={draft.sitemap_include_posts}
          onChange={(v) => update("sitemap_include_posts", v)}
          disabled={isDisabled}
        />
        <BooleanToggle
          label="Include pages"
          value={draft.sitemap_include_pages}
          onChange={(v) => update("sitemap_include_pages", v)}
          disabled={isDisabled}
        />
      </SettingsSection>

      <SettingsSection
        title="Indexing (Robots)"
        description="Which archive pages search engines should not index."
      >
        <BooleanToggle
          label="No-index search results"
          help="Keeps internal search pages out of search engines."
          value={draft.noindex_search}
          onChange={(v) => update("noindex_search", v)}
          disabled={isDisabled}
        />
        <BooleanToggle
          label="No-index author archives"
          value={draft.noindex_author_archives}
          onChange={(v) => update("noindex_author_archives", v)}
          disabled={isDisabled}
        />
        <BooleanToggle
          label="No-index date archives"
          value={draft.noindex_date_archives}
          onChange={(v) => update("noindex_date_archives", v)}
          disabled={isDisabled}
        />
        <BooleanToggle
          label="No-index empty product categories"
          value={draft.noindex_empty_category}
          onChange={(v) => update("noindex_empty_category", v)}
          disabled={isDisabled}
        />
      </SettingsSection>

      <SettingsSection
        title="Breadcrumbs"
        description="Enable or disable breadcrumb navigation on the front-end."
      >
        <BooleanToggle
          label="Enable breadcrumbs"
          help="Requires theme support or manual code placement."
          value={draft.breadcrumbs_enabled}
          onChange={(v) => update("breadcrumbs_enabled", v)}
          disabled={isDisabled}
        />
        <BooleanToggle
          label="Breadcrumbs on products"
          value={draft.wc_show_product_breadcrumbs}
          onChange={(v) => update("wc_show_product_breadcrumbs", v)}
          disabled={isDisabled}
        />
      </SettingsSection>

      <SettingsSection
        title="WooCommerce"
        description="WooCommerce-specific SEO behaviors."
      >
        <BooleanToggle
          label="Remove product category base"
          help="Changes URLs from /product-category/ to a shorter form."
          value={draft.wc_remove_category_base}
          onChange={(v) => update("wc_remove_category_base", v)}
          disabled={isDisabled}
        />
      </SettingsSection>
    </div>
  );
}