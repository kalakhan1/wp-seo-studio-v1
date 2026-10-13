import { useState } from "react";
import {
  AlertTriangle,
  Download,
  FileWarning,
  Loader2,
  Upload,
} from "lucide-react";
import { toast } from "sonner";

import { backupApi } from "@/services/backupApi";
import type { BackupBundle, BackupImportReport } from "@/types/backup";
import { ApiError } from "@/types/errors";

export function BackupPage(): JSX.Element {
  const [exporting, setExporting] = useState(false);
  const [importing, setImporting] = useState(false);
  const [bundleText, setBundleText] = useState("");
  const [report, setReport] = useState<BackupImportReport | null>(null);
  const [includeConnections, setIncludeConnections] = useState(true);
  const [includeTemplates, setIncludeTemplates] = useState(true);
  const [includeSettings, setIncludeSettings] = useState(true);

  const handleExport = async (): Promise<void> => {
    setExporting(true);
    try {
      const res = await backupApi.exportBundle();
      const text = JSON.stringify(res.bundle, null, 2);
      setBundleText(text);
      const blob = new Blob([text], { type: "application/json;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      a.download = `wp-seo-studio-backup-${ts}.json`;
      a.click();
      URL.revokeObjectURL(url);
      res.warnings.forEach((w) => toast.info(w));
      toast.success("Backup exported.");
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Export failed: ${err.message}`);
      } else {
        toast.error("Export failed.");
      }
    } finally {
      setExporting(false);
    }
  };

  const parseBundle = (): BackupBundle | null => {
    try {
      const parsed = JSON.parse(bundleText) as BackupBundle;
      if (parsed.format !== "wp-seo-studio.backup.v1") {
        toast.error("Unrecognized backup format.");
        return null;
      }
      return parsed;
    } catch {
      toast.error("Could not parse the backup JSON.");
      return null;
    }
  };

  const handlePreview = async (): Promise<void> => {
    const bundle = parseBundle();
    if (!bundle) return;
    setImporting(true);
    try {
      const res = await backupApi.importBundle({
        bundle,
        dry_run: true,
        include_connections: includeConnections,
        include_prompt_templates: includeTemplates,
        include_app_settings: includeSettings,
      });
      setReport(res);
      toast.info("Preview generated. Review before applying.");
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Preview failed: ${err.message}`);
      } else {
        toast.error("Preview failed.");
      }
    } finally {
      setImporting(false);
    }
  };

  const handleApply = async (): Promise<void> => {
    const bundle = parseBundle();
    if (!bundle) return;
    if (
      !window.confirm(
        "Apply this import? Existing connections with the same label will be skipped. Prompt templates and app settings may be overwritten.",
      )
    ) {
      return;
    }
    setImporting(true);
    try {
      const res = await backupApi.importBundle({
        bundle,
        dry_run: false,
        include_connections: includeConnections,
        include_prompt_templates: includeTemplates,
        include_app_settings: includeSettings,
      });
      setReport(res);
      toast.success("Import applied. Review the report below.");
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Import failed: ${err.message}`);
      } else {
        toast.error("Import failed.");
      }
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-800">
          Backup and Restore
        </h1>
        <p className="text-sm text-slate-500">
          Export and import the application's non-secret configuration:
          connection metadata, prompt templates, and non-secret settings.
        </p>
      </div>

      {/* Scope warning */}
      <div className="rounded-lg border border-warning bg-warning-light/30 p-4">
        <div className="mb-1 flex items-center gap-2 text-sm font-semibold text-warning">
          <AlertTriangle className="h-4 w-4" />
          Important: scope and limits
        </div>
        <ul className="ml-6 list-disc space-y-1 text-xs text-slate-700">
          <li>
            This is NOT a WordPress backup. It does not include posts, pages,
            products, media, or site settings.
          </li>
          <li>
            Secrets (application passwords, WooCommerce keys, AI keys) are
            never exported or imported. They live only in your OS keyring.
          </li>
          <li>
            After importing, you must re-add credentials to any connection
            whose secret is missing.
          </li>
        </ul>
      </div>

      {/* Export */}
      <section className="rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-3 text-base font-semibold text-slate-800">
          Export configuration
        </h2>
        <p className="mb-3 text-xs text-slate-500">
          Downloads a JSON file. Includes connection metadata (not secrets),
          prompt templates, and non-secret app settings.
        </p>
        <button
          type="button"
          onClick={() => void handleExport()}
          disabled={exporting}
          className="inline-flex items-center gap-2 rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
        >
          {exporting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Download className="h-4 w-4" />
          )}
          {exporting ? "Exporting…" : "Export backup"}
        </button>
      </section>

      {/* Import */}
      <section className="rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-3 text-base font-semibold text-slate-800">
          Import configuration
        </h2>
        <p className="mb-3 text-xs text-slate-500">
          Paste a previously exported JSON file. Always preview before
          applying.
        </p>

        <label className="mb-3 flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={includeConnections}
            onChange={(e) => setIncludeConnections(e.target.checked)}
            className="h-4 w-4 rounded border-surface-border"
          />
          Include connections
        </label>
        <label className="mb-3 flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={includeTemplates}
            onChange={(e) => setIncludeTemplates(e.target.checked)}
            className="h-4 w-4 rounded border-surface-border"
          />
          Include prompt templates
        </label>
        <label className="mb-3 flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={includeSettings}
            onChange={(e) => setIncludeSettings(e.target.checked)}
            className="h-4 w-4 rounded border-surface-border"
          />
          Include app settings
        </label>

        <textarea
          value={bundleText}
          onChange={(e) => setBundleText(e.target.value)}
          rows={10}
          placeholder='Paste the JSON content of a backup file here.'
          className="mb-3 block w-full rounded border border-surface-border bg-white p-3 font-mono text-xs shadow-sm focus:outline-none focus:ring-2 focus:ring-brand"
          spellCheck={false}
        />

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void handlePreview()}
            disabled={importing || !bundleText.trim()}
            className="inline-flex items-center gap-2 rounded border border-brand px-4 py-2 text-sm font-medium text-brand hover:bg-brand-light disabled:opacity-50"
          >
            <FileWarning className="h-4 w-4" />
            Preview (dry run)
          </button>
          <button
            type="button"
            onClick={() => void handleApply()}
            disabled={importing || !bundleText.trim() || !report?.dry_run}
            className="inline-flex items-center gap-2 rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
          >
            {importing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Upload className="h-4 w-4" />
            )}
            Apply import
          </button>
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Apply is disabled until a successful preview has run.
        </p>
      </section>

      {/* Report */}
      {report ? (
        <section className="rounded-lg border border-surface-border bg-white p-5">
          <h2 className="mb-3 text-base font-semibold text-slate-800">
            {report.dry_run ? "Preview report" : "Import report"}
          </h2>
          <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            <Stat label="Connections created" value={report.connections_created} />
            <Stat label="Connections skipped" value={report.connections_skipped} />
            <Stat
              label="Templates updated"
              value={report.prompt_templates_updated}
            />
            <Stat
              label="Settings updated"
              value={report.app_settings_updated}
            />
          </dl>

          {report.warnings.length > 0 ? (
            <div className="mt-4 rounded border border-warning bg-warning-light/30 p-3">
              <p className="mb-1 text-xs font-semibold text-warning">
                Warnings
              </p>
              <ul className="ml-4 list-disc text-xs text-slate-700">
                {report.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {report.errors.length > 0 ? (
            <div className="mt-3 rounded border border-danger bg-danger-light/30 p-3">
              <p className="mb-1 text-xs font-semibold text-danger">Errors</p>
              <ul className="ml-4 list-disc text-xs text-slate-700">
                {report.errors.map((e, i) => (
                  <li key={i}>{e}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }): JSX.Element {
  return (
    <div className="rounded border border-surface-border px-3 py-2">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className="text-lg font-semibold text-slate-800">{value}</p>
    </div>
  );
}