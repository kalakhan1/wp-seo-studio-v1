import { useCallback, useEffect, useState } from "react";
import { Package, Plus, RefreshCw, Truck } from "lucide-react";
import { toast } from "sonner";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingPage } from "@/components/feedback/Loading";
import { ZoneCard } from "@/features/shipping/ZoneCard";
import { ZoneForm } from "@/features/shipping/ZoneForm";
import { connectionApi } from "@/services/connectionApi";
import { wcShippingApi } from "@/services/wcShippingApi";
import type { Connection } from "@/types/connection";
import type {
  WCAvailableMethod,
  WCShippingZoneDetail,
} from "@/types/wcShipping";
import { ApiError } from "@/types/errors";

export function ShippingPage(): JSX.Element {
  const [connections, setConnections] = useState<Connection[] | null>(null);
  const [activeConnectionId, setActiveConnectionId] = useState<number | null>(
    null,
  );
  const [details, setDetails] = useState<WCShippingZoneDetail[] | null>(null);
  const [available, setAvailable] = useState<WCAvailableMethod[]>([]);
  const [loading, setLoading] = useState(false);
  const [showZoneForm, setShowZoneForm] = useState(false);
  const [confirmDeleteZone, setConfirmDeleteZone] = useState<number | null>(
    null,
  );

  // Load connections
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
      const [zonesRes, methodsRes] = await Promise.all([
        wcShippingApi.listZones(activeConnectionId),
        wcShippingApi.listAvailableMethods(activeConnectionId),
      ]);
      setAvailable(methodsRes.items);
      const loaded = await Promise.all(
        zonesRes.items.map((z) =>
          wcShippingApi.getZone(activeConnectionId, z.id),
        ),
      );
      setDetails(loaded);
    } catch (err) {
      setDetails([]);
      if (err instanceof ApiError) {
        toast.error(`Failed to load shipping zones: ${err.message}`);
      } else {
        toast.error("Failed to load shipping zones.");
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

  const handleDeleteZone = async (): Promise<void> => {
    if (confirmDeleteZone === null || activeConnectionId === null) return;
    const zoneId = confirmDeleteZone;
    setConfirmDeleteZone(null);
    try {
      await wcShippingApi.deleteZone(activeConnectionId, zoneId);
      toast.success("Zone deleted.");
      void reload();
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Delete failed: ${err.message}`);
      } else {
        toast.error("Delete failed.");
      }
    }
  };

  if (connections === null) {
    return <LoadingPage label="Loading…" />;
  }

  if (connections.length === 0) {
    return (
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-6 text-2xl font-semibold text-slate-800">
          Shipping Zones
        </h1>
        <EmptyState
          title="Add a connection first"
          description="Shipping zones require a WordPress connection with WooCommerce REST API keys."
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
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-slate-800">
          Shipping Zones
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
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <button
            type="button"
            onClick={() => setShowZoneForm(true)}
            className="inline-flex items-center gap-1.5 rounded bg-brand px-3 py-2 text-sm font-medium text-white hover:bg-brand-dark"
          >
            <Plus className="h-4 w-4" />
            New zone
          </button>
        </div>
      </div>

      {loading && details === null ? (
        <LoadingPage label="Loading shipping zones…" />
      ) : details && details.length > 0 ? (
        <div className="space-y-3">
          {details.map((detail) => (
            <ZoneCard
              key={detail.zone.id}
              detail={detail}
              availableMethods={available}
              connectionId={activeConnectionId as number}
              onChanged={() => void reload()}
              onDelete={(zoneId) => setConfirmDeleteZone(zoneId)}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          title="No shipping zones yet"
          description="Add a zone to define where you ship and what methods are available."
          icon={<Truck className="h-10 w-10" />}
          action={
            <button
              type="button"
              onClick={() => setShowZoneForm(true)}
              className="rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
            >
              Create first zone
            </button>
          }
        />
      )}

      {showZoneForm && activeConnectionId !== null ? (
        <ZoneForm
          connectionId={activeConnectionId}
          onClose={() => setShowZoneForm(false)}
          onSaved={() => {
            setShowZoneForm(false);
            void reload();
          }}
        />
      ) : null}

      <ConfirmDialog
        open={confirmDeleteZone !== null}
        title="Delete this shipping zone?"
        description="The zone and its methods will be permanently removed from WooCommerce. This cannot be undone."
        confirmLabel="Delete"
        variant="danger"
        onConfirm={() => void handleDeleteZone()}
        onCancel={() => setConfirmDeleteZone(null)}
      />
    </div>
  );
}