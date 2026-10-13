import { useCallback, useEffect, useState } from "react";
import {
  CheckCircle2,
  Loader2,
  Plug,
  RefreshCw,
  Trash2,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingPage } from "@/components/feedback/Loading";
import { CapabilityPanel } from "@/features/connection/CapabilityPanel";
import { ConnectionForm } from "@/features/connection/ConnectionForm";
import { connectionApi } from "@/services/connectionApi";
import type { CapabilityReport } from "@/types/capability";
import type { Connection } from "@/types/connection";
import { ApiError } from "@/types/errors";

type Mode = "list" | "new";

export function ConnectionPage(): JSX.Element {
  const [mode, setMode] = useState<Mode>("list");
  const [connections, setConnections] = useState<Connection[] | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [report, setReport] = useState<CapabilityReport | null>(null);
  const [reportFor, setReportFor] = useState<Connection | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<Connection | null>(null);

  const reload = useCallback(async () => {
    try {
      const res = await connectionApi.list();
      setConnections(res.connections);
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Failed to load connections: ${err.message}`);
      } else {
        toast.error("Failed to load connections.");
      }
      setConnections([]);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const handleVerify = async (c: Connection): Promise<void> => {
    setBusyId(c.id);
    try {
      const res = await connectionApi.verify(c.id);
      if (res.ok) {
        toast.success(`Verified "${c.label}".`);
      } else {
        toast.error(`Verification failed for "${c.label}": ${res.message}`);
      }
      await reload();
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Verify failed: ${err.message}`);
      } else {
        toast.error("Verify failed.");
      }
    } finally {
      setBusyId(null);
    }
  };

  const handleDiscover = async (c: Connection): Promise<void> => {
    setBusyId(c.id);
    try {
      const res = await connectionApi.discover(c.id);
      setReport(res);
      setReportFor(c);
      toast.success("Capability discovery complete.");
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Discovery failed: ${err.message}`);
      } else {
        toast.error("Discovery failed.");
      }
    } finally {
      setBusyId(null);
    }
  };

  const handleDelete = async (): Promise<void> => {
    if (!confirmDelete) return;
    const c = confirmDelete;
    setConfirmDelete(null);
    try {
      await connectionApi.remove(c.id);
      toast.success(`Deleted "${c.label}".`);
      if (reportFor?.id === c.id) {
        setReport(null);
        setReportFor(null);
      }
      await reload();
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Delete failed: ${err.message}`);
      } else {
        toast.error("Delete failed.");
      }
    }
  };

  if (mode === "new") {
    return (
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-6 text-2xl font-semibold text-slate-800">
          Website Connection
        </h1>
        <ConnectionForm
          onSaved={() => {
            setMode("list");
            void reload();
          }}
          onCancel={() => setMode("list")}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-800">
          Website Connection
        </h1>
        <button
          type="button"
          onClick={() => setMode("new")}
          className="rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
        >
          New Connection
        </button>
      </div>

      {connections === null ? (
        <LoadingPage label="Loading connections…" />
      ) : connections.length === 0 ? (
        <EmptyState
          title="No connections yet"
          description="Add a WordPress connection to start discovering capabilities, publishing content, and managing your store."
          icon={<Plug className="h-10 w-10" />}
          action={
            <button
              type="button"
              onClick={() => setMode("new")}
              className="rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
            >
              Add your first connection
            </button>
          }
        />
      ) : (
        <div className="space-y-3">
          {connections.map((c) => (
            <div
              key={c.id}
              className="rounded-lg border border-surface-border bg-white p-4"
            >
              <div className="mb-3 flex flex-wrap items-center gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-slate-800">{c.label}</h3>
                    {c.last_verified_ok ? (
                      <span
                        className="inline-flex items-center gap-1 rounded-full bg-success-light px-2 py-0.5 text-xs font-medium text-success"
                        title={`Last verified: ${c.last_verified_at ?? ""}`}
                      >
                        <CheckCircle2 className="h-3 w-3" /> verified
                      </span>
                    ) : c.last_verified_at ? (
                      <span
                        className="inline-flex items-center gap-1 rounded-full bg-danger-light px-2 py-0.5 text-xs font-medium text-danger"
                        title={`Last verified: ${c.last_verified_at}`}
                      >
                        <XCircle className="h-3 w-3" /> failed
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-1 font-mono text-xs text-slate-500">
                    {c.base_url} · {c.username}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => void handleVerify(c)}
                    disabled={busyId === c.id}
                    className="inline-flex items-center gap-1 rounded border border-surface-border px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-surface-muted disabled:opacity-50"
                  >
                    {busyId === c.id ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <RefreshCw className="h-3 w-3" />
                    )}
                    Verify
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleDiscover(c)}
                    disabled={busyId === c.id}
                    className="inline-flex items-center gap-1 rounded border border-brand px-3 py-1.5 text-xs font-medium text-brand hover:bg-brand-light disabled:opacity-50"
                  >
                    Discover Capabilities
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmDelete(c)}
                    className="inline-flex items-center gap-1 rounded border border-danger px-3 py-1.5 text-xs font-medium text-danger hover:bg-danger-light disabled:opacity-50"
                  >
                    <Trash2 className="h-3 w-3" />
                    Delete
                  </button>
                </div>
              </div>
              <ul className="flex flex-wrap gap-3 text-xs text-slate-500">
                <li>
                  Auth: <span className="font-mono">{c.auth_method}</span>
                </li>
                <li>
                  HTTPS required:{" "}
                  <span className="font-mono">{c.require_https ? "yes" : "no"}</span>
                </li>
                <li>
                  WooCommerce keys:{" "}
                  <span className="font-mono">
                    {c.has_wc_credentials ? "yes" : "no"}
                  </span>
                </li>
              </ul>
            </div>
          ))}
        </div>
      )}

      {report && reportFor ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-800">
              Capability report: {reportFor.label}
            </h2>
            <button
              type="button"
              onClick={() => {
                setReport(null);
                setReportFor(null);
              }}
              className="rounded border border-surface-border px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-surface-muted"
            >
              Close
            </button>
          </div>
          <CapabilityPanel report={report} />
        </div>
      ) : null}

      <ConfirmDialog
        open={confirmDelete !== null}
        title={`Delete connection "${confirmDelete?.label ?? ""}"?`}
        description="The metadata will be removed and stored credentials will be deleted from your OS keyring. This cannot be undone."
        confirmLabel="Delete"
        variant="danger"
        onConfirm={() => void handleDelete()}
        onCancel={() => setConfirmDelete(null)}
      />
    </div>
  );
}