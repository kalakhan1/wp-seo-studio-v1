import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import { toast } from "sonner";

import { LoadingPage } from "@/components/feedback/Loading";
import { PromptEditor } from "@/features/ai-prompt-studio/PromptEditor";
import { aiPromptApi } from "@/services/aiPromptApi";
import type {
  AIStatusResponse,
  PromptTemplate,
  TemplateType,
} from "@/types/aiPrompt";

const TABS: { key: TemplateType; label: string }[] = [
  { key: "product", label: "Product prompt" },
  { key: "blog", label: "Blog prompt" },
];

export function AIPromptStudioPage(): JSX.Element {
  const [status, setStatus] = useState<AIStatusResponse | null>(null);
  const [templates, setTemplates] = useState<PromptTemplate[] | null>(null);
  const [activeTab, setActiveTab] = useState<TemplateType>("product");

  const reload = async (): Promise<void> => {
    try {
      const [s, t] = await Promise.all([
        aiPromptApi.status(),
        aiPromptApi.listTemplates(),
      ]);
      setStatus(s);
      setTemplates(t.items);
    } catch (err) {
      toast.error("Failed to load AI prompt studio.");
      setTemplates([]);
    }
  };

  useEffect(() => {
    void reload();
  }, []);

  if (templates === null) {
    return <LoadingPage label="Loading prompt studio…" />;
  }

  const current = templates.find((t) => t.template_type === activeTab);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold text-slate-800">
            <Sparkles className="h-6 w-6 text-slate-400" />
            AI Prompt Studio
          </h1>
          <p className="text-sm text-slate-500">
            Editable product and blog prompts. Returned JSON is validated
            but never published automatically.
          </p>
        </div>
      </div>

      {/* Provider status */}
      {status ? (
        <div
          className={`rounded-lg border p-4 text-sm ${
            status.available
              ? "border-success bg-success-light/30"
              : "border-warning bg-warning-light/30"
          }`}
        >
          <p className="font-medium text-slate-800">
            Provider: <span className="font-mono">{status.provider}</span>
            {status.model ? (
              <>
                {" · "}
                <span className="font-mono">{status.model}</span>
              </>
            ) : null}
          </p>
          {!status.available && status.reason ? (
            <p className="mt-1 text-slate-700">{status.reason}</p>
          ) : (
            <p className="mt-1 text-slate-700">
              {status.provider === "mock"
                ? "Mock provider is active. Set AI_PROVIDER in .env to use a real provider."
                : "Ready."}
            </p>
          )}
        </div>
      ) : null}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-surface-border">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveTab(tab.key)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? "border-brand text-brand-dark"
                : "border-transparent text-slate-600 hover:text-slate-800"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Editor */}
      {current ? (
        <PromptEditor
          templateType={activeTab}
          initial={current}
          onUpdated={(t) => {
            setTemplates((prev) =>
              prev ? prev.map((p) => (p.id === t.id ? t : p)) : prev,
            );
          }}
        />
      ) : (
        <p className="text-sm text-slate-500">
          No template found for {activeTab}.
        </p>
      )}
    </div>
  );
}