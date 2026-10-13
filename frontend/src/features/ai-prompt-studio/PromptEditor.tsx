import { useEffect, useState } from "react";
import { Copy, RotateCcw, Save, Send, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { aiPromptApi } from "@/services/aiPromptApi";
import type { PromptTemplate, TemplateType } from "@/types/aiPrompt";
import { ApiError } from "@/types/errors";

interface PromptEditorProps {
  templateType: TemplateType;
  initial: PromptTemplate;
  onUpdated: (t: PromptTemplate) => void;
}

export function PromptEditor({
  templateType,
  initial,
  onUpdated,
}: PromptEditorProps): JSX.Element {
  const [content, setContent] = useState(initial.content);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [lastGeneration, setLastGeneration] = useState<string>("");

  useEffect(() => {
    setContent(initial.content);
  }, [initial]);

  const dirty = content !== initial.content;

  const handleSave = async (): Promise<void> => {
    setSaving(true);
    try {
      const updated = await aiPromptApi.updateTemplate(templateType, content);
      toast.success("Template saved.");
      onUpdated(updated);
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

  const handleRestore = async (): Promise<void> => {
    if (!window.confirm("Restore the default template? Your customizations will be lost.")) {
      return;
    }
    try {
      const res = await aiPromptApi.restoreTemplate(templateType);
      toast.success("Default template restored.");
      setContent(res.template.content);
      onUpdated(res.template);
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Restore failed: ${err.message}`);
      } else {
        toast.error("Restore failed.");
      }
    }
  };

  const handleCopy = async (): Promise<void> => {
    try {
      await navigator.clipboard.writeText(content);
      toast.success("Prompt copied to clipboard.");
    } catch {
      toast.error("Could not copy. Select and copy manually.");
    }
  };

  const handleExport = (): void => {
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${templateType}-prompt.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleGenerate = async (): Promise<void> => {
    setGenerating(true);
    setLastGeneration("");
    try {
      const res = await aiPromptApi.generate(content, templateType);
      if (!res.ok) {
        toast.error(`AI request failed: ${res.parse_error || "unknown error"}`);
      } else {
        setLastGeneration(res.raw_response);
        if (res.parse_error) {
          toast.warning("Response received but JSON could not be parsed.");
        } else {
          toast.success(`Response received from ${res.provider}.`);
        }
        res.warnings.forEach((w) => toast.info(w));
      }
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Request failed: ${err.message}`);
      } else {
        toast.error("Request failed.");
      }
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-surface-border bg-white px-4 py-3">
        <p className="text-sm text-slate-600">
          {dirty ? "Unsaved changes." : initial.is_default ? "Using shipped default." : "Customized."}
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void handleCopy()}
            className="inline-flex items-center gap-1.5 rounded border border-surface-border px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-surface-muted"
          >
            <Copy className="h-3 w-3" />
            Copy
          </button>
          <button
            type="button"
            onClick={handleExport}
            className="inline-flex items-center gap-1.5 rounded border border-surface-border px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-surface-muted"
          >
            Export
          </button>
          <button
            type="button"
            onClick={() => void handleRestore()}
            className="inline-flex items-center gap-1.5 rounded border border-surface-border px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-surface-muted"
          >
            <RotateCcw className="h-3 w-3" />
            Restore default
          </button>
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={saving || !dirty}
            className="inline-flex items-center gap-1.5 rounded bg-brand px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-dark disabled:opacity-50"
          >
            <Save className="h-3 w-3" />
            {saving ? "Saving…" : "Save template"}
          </button>
          <button
            type="button"
            onClick={() => void handleGenerate()}
            disabled={generating}
            className="inline-flex items-center gap-1.5 rounded border border-brand px-3 py-1.5 text-xs font-medium text-brand hover:bg-brand-light disabled:opacity-50"
          >
            <Sparkles className="h-3 w-3" />
            {generating ? "Sending…" : "Send to AI"}
          </button>
        </div>
      </div>

      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={22}
        className="block w-full rounded-lg border border-surface-border bg-white p-4 font-mono text-xs shadow-sm focus:outline-none focus:ring-2 focus:ring-brand"
        spellCheck={false}
      />

      {lastGeneration ? (
        <div className="rounded-lg border border-surface-border bg-white p-4">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-800">
              AI response (raw)
            </h3>
            <Send className="h-4 w-4 text-slate-400" />
          </div>
          <pre className="max-h-96 overflow-auto rounded bg-slate-900 p-3 text-xs text-slate-100">
            {lastGeneration}
          </pre>
          <p className="mt-2 text-xs text-slate-500">
            This is the raw provider output. It is not saved anywhere and is
            not published automatically.
          </p>
        </div>
      ) : null}
    </div>
  );
}