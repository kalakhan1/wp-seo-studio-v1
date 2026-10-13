import { useCallback, useEffect, useState } from "react";
import { Package, RefreshCw } from "lucide-react";
import { toast } from "sonner";

import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingPage } from "@/components/feedback/Loading";
import { CODStatusCard } from "@/features/cod/CODStatusCard";
import { CODForm } from "@/features/cod/CODForm";
import { connectionApi } from "@/services/connectionApi";
import { wcGatewayApi } from "@/services/wcGatewayApi";
import type { Connection } from "@/types/connection";
import type { CODStatus } from "@/types/wcGateway";
import { ApiError } from "@/types/errors";

export function CODPage(): JSX.Element {
  const [connections, setConnections] = useState<Connection[] | null>(null);
  const [activeConnectionId, setActiveConnectionId] = useState<number | null>(
    null,
  );
  const [status, setStatus] = useState<CODStatus | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        const res = await connectionApi.list();
        setConnections(res.connections);
        const withWc = res.connections.find((c) => c.has_wc_credentials);
        const first = withWc ?? res.connections[0];
        if (first) setActiveConnectionId(first.id);
      } catch {
        toast.error("Failed to load connections.");
        setConnections([]);
      }
    })();
  }, []);

  const reload = useCallback(async () => {
    if (activeConnectionId === null) return;
    setLoading(true);
    try {
      const res = await wcGatewayApi.getCOD(activeConnectionId);
      setStatus(res);
    } catch (err) {
      setStatus(null);
      if (err instanceof ApiError) {
        toast.error(`Failed to load COD status: ${err.message}`);
      } else {
        toast.error("Failed to load COD status.");
      }
    } finally {
      setLoading(false);
    }
  }, [activeConnectionId]);

  useEffect(() => {
    if (activeConnectionId !== null) {
      void reload();
    }
  }, [activeConnectionId, reload]);

  if (connections === null) {
    return <LoadingPage label="Loading…" />;
  }

  if (connections.length === 0) {
    return (
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-6 text-2xl font-semibold text-slate-800">
          Cash on Delivery
        </h1>
        <EmptyState
          title="Add a connection first"
          description="COD configuration requires a WordPress connection with WooCommerce REST API keys."
          icon={<Package className="h-10 w-10" />}
          action={
            <a
              href="/connection"
              className="rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
            >
              Go to Website Connection
            </a>
          }
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-slate-800">
          Cash on Delivery
        </h1>
        <div className="flex items-center gap-2">
          {connections.length > 1 ? (
            <select
              value={activeConnectionId?.toString() ?? ""}
              onChange={(e) => setActiveConnectionId(Number(e.target.value))}
              className="rounded border border-surface-border bg-white px-3 py-2 text-sm"
            >
              {connections.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          ) : null}
          <button
            type="button"
            onClick={() => void reload()}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded border border-surface-border px-3 py-2 text-sm font-medium text-slate-700 hover:bg-surface-muted disabled:opacity-50"
          >
            <RefreshCw
              className={`h-4 w-4 ${loading ? "animate-spin" : ""}`}
            />
            Refresh
          </button>
        </div>
      </div>

      {loading && !status ? (
        <LoadingPage label="Loading COD status…" />
      ) : status ? (
        <>
          <CODStatusCard status={status} />
          <CODForm
            connectionId={activeConnectionId as number}
            status={status}
            onSaved={() => void reload()}
            disabled={loading}
          />
        </>
      ) : null}
    </div>
  );
}