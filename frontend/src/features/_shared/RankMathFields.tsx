import { TextField } from "@/components/inputs/TextField";
import { TextArea } from "@/components/inputs/TextArea";
import type { RankMathMeta } from "@/types/content";

interface RankMathFieldsProps {
  value: RankMathMeta;
  onChange: (next: RankMathMeta) => void;
  disabled?: boolean;
}

const ROBOTS_OPTIONS = [
  { value: "index", label: "index" },
  { value: "noindex", label: "noindex" },
  { value: "follow", label: "follow" },
  { value: "nofollow", label: "nofollow" },
  { value: "noarchive", label: "noarchive" },
  { value: "nosnippet", label: "nosnippet" },
  { value: "noimageindex", label: "noimageindex" },
];

export function RankMathFields({
  value,
  onChange,
  disabled = false,
}: RankMathFieldsProps): JSX.Element {
  const update = <K extends keyof RankMathMeta>(
    key: K,
    v: RankMathMeta[K],
  ): void => {
    onChange({ ...value, [key]: v });
  };

  const robots = value.robots ?? [];

  const toggleRobot = (r: string): void => {
    const next = robots.includes(r)
      ? robots.filter((x) => x !== r)
      : [...robots, r];
    update("robots", next);
  };

  return (
    <div className="space-y-1">
      <p className="mb-3 text-xs text-slate-500">
        Rank Math fields are written via the companion plugin. If the plugin
        is not installed, the content is still saved and a warning is shown.
      </p>

      <TextField
        label="SEO title"
        value={value.title ?? ""}
        onChange={(v) => update("title", v)}
        placeholder="Example: Herbal Hair Oil for Daily Care"
        help="Shown in search results. Recommended: 50–60 characters."
        maxLength={80}
        showCounter
        disabled={disabled}
      />

      <TextArea
        label="Meta description"
        value={value.description ?? ""}
        onChange={(v) => update("description", v)}
        placeholder="Example: Natural herbal hair oil for daily care."
        help="Shown under the title in search results. Recommended: 150–160 characters."
        rows={3}
        maxLength={200}
        showCounter
        disabled={disabled}
      />

      <TextField
        label="Focus keyword"
        value={value.focus_keyword ?? ""}
        onChange={(v) => update("focus_keyword", v)}
        placeholder="Example: herbal hair oil"
        help="The primary keyword you want this content to rank for."
        disabled={disabled}
      />

      <TextField
        label="Canonical URL"
        value={value.canonical_url ?? ""}
        onChange={(v) => update("canonical_url", v)}
        placeholder="Example: https://example.com/herbal-hair-oil/"
        help="Optional. Leave empty to use the content's own URL."
        type="url"
        disabled={disabled}
      />

      <div className="mb-4">
        <p className="mb-1 block text-sm font-medium text-slate-700">
          Robots directives
        </p>
        <div className="flex flex-wrap gap-2">
          {ROBOTS_OPTIONS.map((opt) => (
            <label
              key={opt.value}
              className={`inline-flex cursor-pointer items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                robots.includes(opt.value)
                  ? "border-brand bg-brand-light text-brand-dark"
                  : "border-surface-border bg-white text-slate-600 hover:bg-surface-muted"
              }`}
            >
              <input
                type="checkbox"
                checked={robots.includes(opt.value)}
                onChange={() => toggleRobot(opt.value)}
                className="hidden"
              />
              {opt.label}
            </label>
          ))}
        </div>
        <p className="mt-1 text-xs text-slate-500">
          Leave empty to use Rank Math defaults. Add `index, follow` to force
          indexing for this item only.
        </p>
      </div>
    </div>
  );
}