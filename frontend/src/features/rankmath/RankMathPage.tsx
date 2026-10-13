import { useCallback, useEffect, useState } from "react";
import { Package, RefreshCw, Search } from "lucide-react";
import { toast } from "sonner";

import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingPage } from "@/components/feedback/Loading";
import { RankMathSettingsForm } from "@/features/rankmath/RankMathSettingsForm";
import { RankMathStatusCard } from "@/features/rankmath/RankMathStatusCard";
import { connectionApi } from "@/services/connectionApi";
import { rankmathSettingsApi } from "@/services/rankmathSettingsApi";
import type { Connection } from "@/types/connection";
import type {
  RankMathCapabilityStatus,
  RankMathSettingsResponse,
} from "@/types/rankmathSettings";
import { ApiError } from "@/types/errors";

export function RankMathPage(): JSX.Element {
  const [connections, setConnections] = useState<Connection[] | null>(null);
  const [activeConnectionId, setActiveConnectionId] = useState<number | null>(
    null,
  );
  const [status, setStatus] = useState<RankMathCapabilityStatus | null>(null);
  const [data, setData] = useState<RankMathSettingsResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        const res = await connectionApi.list();
        setConnections(res.connections);
        const withWp = res.connections[0];
        if (withWp) setActiveConnectionId(withWp.id);
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
      const [s, d] = await Promise.all([
        rankmathSettingsApi.getStatus(activeConnectionId),
        rankmathSettingsApi.getSettings(activeConnectionId),
      ]);
      setStatus(s);
      setData(d);
    } catch (err) {
      setStatus(null);
      setData(null);
      if (err instanceof ApiError) {
        toast.error(`Failed to load: ${err.message}`);
      } else {
        toast.error("Failed to load Rank Math settings.");
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
          Rank Math SEO
        </h1>
        <EmptyState
          title="Add a connection first"
          description="Rank Math settings require a WordPress connection."
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

  const readyForEditing =
    status?.plugin_available === true && status?.rank_math_active === true;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold text-slate-800">
            <Search className="h-6 w-6 text-slate-400" />
            Rank Math SEO
          </h1>
          <p className="text-sm text-slate-500">
            Global settings for titles, sitemaps, indexing, and WooCommerce
            SEO. Per-content fields remain inside each Publisher form.
          </p>
        </div>
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
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {loading && !status ? (
        <LoadingPage label="Loading Rank Math status…" />
      ) : status ? (
        <RankMathStatusCard status={status} />
      ) : null}

      {!readyForEditing ? (
        <div className="rounded-lg border border-warning bg-warning-light/30 p-5 text-sm text-slate-800">
          <p className="mb-2 font-medium">Global settings are read-only.</p>
          <p>
            Install and activate the WP SEO Control Companion plugin on the
            connected WordPress site, and make sure Rank Math is active.
            Once both are in place, the fields below become editable.
          </p>
        </div>
      ) : null}

      {data?.source === "companion" ? (
        <RankMathSettingsForm
          connectionId={activeConnectionId as number}
          settings={data.settings}
          onSaved={(updated) => {
            setData({ ...data, settings: updated });
          }}
          disabled={!readyForEditing}
        />
      ) : data ? (
        <div className="rounded-lg border border-surface-border bg-white p-5 text-sm text-slate-600">
          <p>{data.reason || "Rank Math settings are not available."}</p>
        </div>
      ) : null}
    </div>
  );
}