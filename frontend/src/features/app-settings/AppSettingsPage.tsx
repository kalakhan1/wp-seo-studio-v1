import { useEffect, useState } from "react";
import { toast } from "sonner";

import { LoadingPage } from "@/components/feedback/Loading";
import { SelectField, type SelectOption } from "@/components/inputs/SelectField";
import { useAppSettings } from "@/hooks/useAppSettings";
import type { AppSettings } from "@/types/api";
import { ApiError, NetworkError } from "@/types/errors";

const LOG_LEVELS: SelectOption[] = [
  { value: "debug", label: "debug" },
  { value: "info", label: "info" },
  { value: "warning", label: "warning" },
  { value: "error", label: "error" },
  { value: "critical", label: "critical" },
];

type LogLevel = AppSettings["log_level"];

export function AppSettingsPage(): JSX.Element {
  const { settings, loading, error, update, refresh } = useAppSettings();

  const [logLevel, setLogLevel] = useState<LogLevel>("info");
  const [saving, setSaving] = useState<boolean>(false);

  useEffect(() => {
    if (settings) setLogLevel(settings.log_level);
  }, [settings]);

  const handleSave = async (): Promise<void> => {
    if (!settings) return;
    if (logLevel === settings.log_level) {
      toast.info("No changes to save.");
      return;
    }
    setSaving(true);
    try {
      const updated = await update({ log_level: logLevel });
      toast.success(`Log level updated to "${updated.log_level}".`);
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Save failed: ${err.message}`);
      } else if (err instanceof NetworkError) {
        toast.error(`Network error: ${err.message}`);
      } else {
        toast.error("Save failed.");
      }
    } finally {
      setSaving(false);
    }
  };

  const handleReset = (): void => {
    if (settings) setLogLevel(settings.log_level);
  };

  if (loading || !settings) {
    return <LoadingPage label="Loading settings…" />;
  }

  const dirty = logLevel !== settings.log_level;

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-6 text-2xl font-semibold text-slate-800">App Settings</h1>

      {error ? (
        <div className="mb-4 rounded border border-danger-light bg-danger-light/40 px-3 py-2 text-sm text-danger">
          {error}
          <button
            type="button"
            onClick={() => void refresh()}
            className="ml-2 underline"
          >
            Retry
          </button>
        </div>
      ) : null}

      <section className="mb-6 rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-4 text-base font-semibold text-slate-800">
          Runtime Settings
        </h2>

        <SelectField
          label="Log Level"
          value={logLevel}
          onChange={(v) => setLogLevel(v as LogLevel)}
          options={LOG_LEVELS}
          help="Controls backend log verbosity. Takes effect immediately."
        />

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={handleReset}
            disabled={!dirty || saving}
            className="rounded border border-surface-border px-4 py-2 text-sm font-medium text-slate-700 hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-50"
          >
            Reset
          </button>
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={!dirty || saving}
            className="rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </section>

      <section className="rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-4 text-base font-semibold text-slate-800">
          Read-only Information
        </h2>
        <p className="mb-3 text-xs text-slate-500">
          These values come from the backend environment. Change them in the
          <code className="mx-1 rounded bg-surface-muted px-1 py-0.5 font-mono text-[11px]">
            .env
          </code>
          file and restart the backend.
        </p>
        <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
          <ReadOnlyRow label="Environment" value={settings.app_env} />
          <ReadOnlyRow label="Mode" value={settings.app_mode} />
          <ReadOnlyRow label="Log Format" value={settings.log_format} />
          <ReadOnlyRow label="AI Provider" value={settings.ai_provider} />
          <ReadOnlyRow
            label="Image Search Provider"
            value={settings.image_search_provider}
          />
          <ReadOnlyRow
            label="HTTP Timeout"
            value={`${settings.http_timeout}s`}
          />
          <ReadOnlyRow
            label="HTTP Max Retries"
            value={String(settings.http_max_retries)}
          />
        </dl>
      </section>
    </div>
  );
}

function ReadOnlyRow({ label, value }: { label: string; value: string }): JSX.Element {
  return (
    <div className="rounded border border-surface-border px-3 py-2">
      <dt className="text-xs uppercase tracking-wide text-slate-400">{label}</dt>
      <dd className="mt-0.5 font-mono text-sm text-slate-800">{value}</dd>
    </div>
  );
}