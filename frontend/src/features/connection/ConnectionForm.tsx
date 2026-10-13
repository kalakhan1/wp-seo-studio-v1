import { useState } from "react";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import { toast } from "sonner";

import { TextField } from "@/components/inputs/TextField";
import { connectionApi } from "@/services/connectionApi";
import type {
  ConnectionSaveRequest,
  ConnectionTestResponse,
} from "@/types/connection";
import { ApiError } from "@/types/errors";

interface ConnectionFormProps {
  onSaved: () => void;
  onCancel: () => void;
}

interface FormState {
  label: string;
  baseUrl: string;
  username: string;
  wpAppPassword: string;
  requireHttps: boolean;
  wcConsumerKey: string;
  wcConsumerSecret: string;
}

const INITIAL: FormState = {
  label: "",
  baseUrl: "",
  username: "",
  wpAppPassword: "",
  requireHttps: true,
  wcConsumerKey: "",
  wcConsumerSecret: "",
};

export function ConnectionForm({
  onSaved,
  onCancel,
}: ConnectionFormProps): JSX.Element {
  const [form, setForm] = useState<FormState>(INITIAL);
  const [testResult, setTestResult] = useState<ConnectionTestResponse | null>(
    null,
  );
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);

  const update = <K extends keyof FormState>(key: K, value: FormState[K]): void => {
    setForm((f) => ({ ...f, [key]: value }));
    setTestResult(null); // invalidate test when fields change
  };

  const handleTest = async (): Promise<void> => {
    if (!form.baseUrl || !form.username || !form.wpAppPassword) {
      toast.error("URL, username, and application password are required.");
      return;
    }
    setTesting(true);
    setTestResult(null);
    try {
      const res = await connectionApi.test({
        base_url: form.baseUrl,
        username: form.username,
        wp_app_password: form.wpAppPassword,
        require_https: form.requireHttps,
        wc_consumer_key: form.wcConsumerKey || undefined,
        wc_consumer_secret: form.wcConsumerSecret || undefined,
      });
      setTestResult(res);
      if (res.ok) {
        toast.success("Connection verified.");
      } else {
        toast.error(res.message || "Connection test failed.");
      }
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Test failed: ${err.message}`);
      } else {
        toast.error("Test failed.");
      }
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async (): Promise<void> => {
    if (!form.label || !form.baseUrl || !form.username || !form.wpAppPassword) {
      toast.error("All required fields must be filled.");
      return;
    }
    setSaving(true);
    try {
      const payload: ConnectionSaveRequest = {
        label: form.label,
        base_url: form.baseUrl,
        username: form.username,
        wp_app_password: form.wpAppPassword,
        require_https: form.requireHttps,
        wc_consumer_key: form.wcConsumerKey || undefined,
        wc_consumer_secret: form.wcConsumerSecret || undefined,
      };
      await connectionApi.save(payload);
      toast.success(`Connection "${form.label}" saved.`);
      onSaved();
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

  return (
    <div className="rounded-lg border border-surface-border bg-white p-6">
      <h2 className="mb-4 text-lg font-semibold text-slate-800">
        New WordPress Connection
      </h2>

      <TextField
        label="Connection label"
        value={form.label}
        onChange={(v) => update("label", v)}
        placeholder="Example: Production Store"
        help="A friendly name to identify this connection. Must be unique."
        required
        maxLength={120}
      />

      <TextField
        label="WordPress base URL"
        value={form.baseUrl}
        onChange={(v) => update("baseUrl", v)}
        placeholder="Example: https://example.com"
        help="No trailing slash. HTTPS is required when Require HTTPS is on."
        type="url"
        required
      />

      <TextField
        label="WordPress username"
        value={form.username}
        onChange={(v) => update("username", v)}
        placeholder="Example: admin"
        help="The WordPress user with rights to create content."
        required
      />

      <TextField
        label="Application Password"
        value={form.wpAppPassword}
        onChange={(v) => update("wpAppPassword", v)}
        placeholder="Example: abcd efgh ijkl mnop"
        help="Generate in WordPress → Users → Profile → Application Passwords. Stored only in your OS keyring, never in our database."
        type="text"
        required
      />

      <label className="mb-4 flex items-center gap-2 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={form.requireHttps}
          onChange={(e) => update("requireHttps", e.target.checked)}
          className="h-4 w-4 rounded border-surface-border"
        />
        Require HTTPS
      </label>

      <details className="mb-4">
        <summary className="cursor-pointer text-sm font-medium text-slate-700">
          WooCommerce (optional)
        </summary>
        <div className="mt-3">
          <TextField
            label="WooCommerce consumer key"
            value={form.wcConsumerKey}
            onChange={(v) => update("wcConsumerKey", v)}
            placeholder="Example: ck_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            help="Generate in WooCommerce → Settings → Advanced → REST API."
          />
          <TextField
            label="WooCommerce consumer secret"
            value={form.wcConsumerSecret}
            onChange={(v) => update("wcConsumerSecret", v)}
            placeholder="Example: cs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            help="Stored only in your OS keyring, never in our database."
          />
        </div>
      </details>

      {testResult ? <TestResultPanel result={testResult} /> : null}

      <div className="mt-6 flex justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="rounded border border-surface-border px-4 py-2 text-sm font-medium text-slate-700 hover:bg-surface-muted"
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={() => void handleTest()}
          disabled={testing || saving}
          className="rounded border border-brand px-4 py-2 text-sm font-medium text-brand hover:bg-brand-light disabled:opacity-50"
        >
          {testing ? (
            <span className="inline-flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" /> Testing…
            </span>
          ) : (
            "Test Connection"
          )}
        </button>
        <button
          type="button"
          onClick={() => void handleSave()}
          disabled={saving || testing || testResult?.ok !== true}
          className="rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save Connection"}
        </button>
      </div>
    </div>
  );
}

function TestResultPanel({
  result,
}: {
  result: ConnectionTestResponse;
}): JSX.Element {
  return (
    <div
      className={`mt-4 rounded border p-4 text-sm ${
        result.ok
          ? "border-success bg-success-light/30"
          : "border-danger bg-danger-light/30"
      }`}
    >
      <div className="mb-2 flex items-center gap-2 font-medium">
        {result.ok ? (
          <>
            <CheckCircle2 className="h-4 w-4 text-success" />
            <span className="text-success">Connection verified</span>
          </>
        ) : (
          <>
            <XCircle className="h-4 w-4 text-danger" />
            <span className="text-danger">Connection failed</span>
          </>
        )}
      </div>

      {result.site_info ? (
        <dl className="mb-2 grid grid-cols-1 gap-1 text-xs text-slate-700 sm:grid-cols-2">
          <div>
            <dt className="text-slate-500">Site name</dt>
            <dd className="font-mono">{result.site_info.name || "—"}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Site URL</dt>
            <dd className="font-mono">{result.site_info.url}</dd>
          </div>
          {result.current_user ? (
            <>
              <div>
                <dt className="text-slate-500">Current user</dt>
                <dd className="font-mono">{result.current_user.name}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Roles</dt>
                <dd className="font-mono">
                  {result.current_user.roles.join(", ") || "—"}
                </dd>
              </div>
            </>
          ) : null}
        </dl>
      ) : null}

      {result.message ? (
        <p className="mb-2 text-slate-700">{result.message}</p>
      ) : null}

      {result.warnings.length > 0 ? (
        <ul className="ml-4 list-disc space-y-0.5 text-xs text-warning">
          {result.warnings.map((w, i) => (
            <li key={i}>{w}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}