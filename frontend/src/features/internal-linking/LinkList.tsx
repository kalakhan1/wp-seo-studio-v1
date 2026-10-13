import { Trash2, Link as LinkIcon, AlertTriangle } from "lucide-react";

import { TextField } from "@/components/inputs/TextField";
import { SelectField } from "@/components/inputs/SelectField";
import type { LinkType } from "@/types/internalLink";

export interface DraftLink {
  id: string;
  url: string;
  anchor: string;
  linkType: LinkType;
  label: string;
  contextNote: string;
  warnings: string[];
}

interface LinkListProps {
  links: DraftLink[];
  onChange: (links: DraftLink[]) => void;
}

const LINK_TYPE_OPTIONS = [
  { value: "contextual", label: "Contextual (inside content)" },
  { value: "related_product", label: "Related product" },
  { value: "related_article", label: "Related article" },
  { value: "category", label: "Category link" },
  { value: "brand", label: "Brand link" },
  { value: "footer_related", label: "Footer related-content section" },
];

export function LinkList({ links, onChange }: LinkListProps): JSX.Element {
  const update = (id: string, patch: Partial<DraftLink>): void => {
    onChange(
      links.map((l) => (l.id === id ? { ...l, ...patch } : l)),
    );
  };

  const remove = (id: string): void => {
    onChange(links.filter((l) => l.id !== id));
  };

  if (links.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-surface-border bg-white p-8 text-center">
        <LinkIcon className="mx-auto mb-2 h-8 w-8 text-slate-300" />
        <p className="text-sm text-slate-600">
          No links yet. Search above or accept a suggestion to add one.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {links.map((link, i) => (
        <div
          key={link.id}
          className="rounded-lg border border-surface-border bg-white p-4"
        >
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-800">
              Link #{i + 1}
            </h3>
            <button
              type="button"
              onClick={() => remove(link.id)}
              className="inline-flex items-center gap-1 rounded border border-danger px-2 py-1 text-xs font-medium text-danger hover:bg-danger-light"
            >
              <Trash2 className="h-3 w-3" />
              Remove
            </button>
          </div>

          <TextField
            label="Target URL"
            value={link.url}
            onChange={(v) => update(link.id, { url: v })}
            placeholder="Example: https://example.com/blog/badam-benefits/"
            help="Must belong to the connected site."
          />

          <TextField
            label="Anchor text"
            value={link.anchor}
            onChange={(v) => update(link.id, { anchor: v })}
            placeholder="Example: badam benefits guide"
            help="Text visible to the reader. Keep it descriptive."
          />

          <SelectField
            label="Link type"
            value={link.linkType}
            onChange={(v) => update(link.id, { linkType: v as LinkType })}
            options={LINK_TYPE_OPTIONS}
          />

          <TextField
            label="Label (optional)"
            value={link.label}
            onChange={(v) => update(link.id, { label: v })}
            placeholder="Example: Read More"
            help="Shown if you use a call-to-action label."
          />

          <TextField
            label="Context note (optional)"
            value={link.contextNote}
            onChange={(v) => update(link.id, { contextNote: v })}
            placeholder="Example: after the paragraph about daily care"
            help="A hint for where this link should appear."
          />

          {link.warnings.length > 0 ? (
            <div className="mt-2 rounded border border-warning bg-warning-light/30 p-2">
              <div className="mb-1 flex items-center gap-1 text-xs font-medium text-warning">
                <AlertTriangle className="h-3 w-3" />
                Warnings
              </div>
              <ul className="ml-4 list-disc text-xs text-slate-700">
                {link.warnings.map((w, j) => (
                  <li key={j}>{w}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}