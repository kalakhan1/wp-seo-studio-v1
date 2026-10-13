import { useCallback, useEffect, useState } from "react";
import {
  CreditCard,
  Globe,
  Package,
  RefreshCw,
  Settings as SettingsIcon,
  Truck,
  Wallet,
} from "lucide-react";
import { toast } from "sonner";

import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingPage } from "@/components/feedback/Loading";
import {
  SetupStepCard,
  type StepStatus,
} from "@/features/site-setup/SetupStepCard";
import { connectionApi } from "@/services/connectionApi";
import { wcGatewayApi } from "@/services/wcGatewayApi";
import { wcSettingsApi } from "@/services/wcSettingsApi";
import { wcShippingApi } from "@/services/wcShippingApi";
import type { Connection } from "@/types/connection";
import type { StoreProfileResponse } from "@/types/wcSettings";
import type { CODStatus } from "@/types/wcGateway";
import { ApiError } from "@/types/errors";

interface Aggregated {
  profile: StoreProfileResponse | null;
  cod: CODStatus | null;
  shippingZoneCount: number;
  connection: Connection | null;
}

export function SetupWizardPage(): JSX.Element {
  const [connections, setConnections] = useState<Connection[] | null>(null);
  const [activeConnectionId, setActiveConnectionId] = useState<number | null>(
    null,
  );
  const [data, setData] = useState<Aggregated | null>(null);
  const [loading, setLoading] = useState(false);

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
    if (activeConnectionId === null || connections === null) return;
    setLoading(true);
    const connection = connections.find((c) => c.id === activeConnectionId);
    if (!connection) {
      setLoading(false);
      return;
    }

    let profile: StoreProfileResponse | null = null;
    let cod: CODStatus | null = null;
    let zoneCount = 0;
    const warnings: string[] = [];

    try {
      profile = await wcSettingsApi.getStoreProfile(activeConnectionId);
    } catch (err) {
      if (err instanceof ApiError) {
        warnings.push(`Store profile: ${err.message}`);
      } else {
        warnings.push("Store profile: could not load.");
      }
    }

    try {
      cod = await wcGatewayApi.getCOD(activeConnectionId);
    } catch (err) {
      if (err instanceof ApiError) {
        warnings.push(`COD: ${err.message}`);
      } else {
        warnings.push("COD: could not load.");
      }
    }

    try {
      const zones = await wcShippingApi.listZones(activeConnectionId);
      zoneCount = zones.items.length;
    } catch (err) {
      if (err instanceof ApiError) {
        warnings.push(`Shipping: ${err.message}`);
      } else {
        warnings.push("Shipping: could not load.");
      }
    }

    if (warnings.length > 0) {
      warnings.forEach((w) => toast.warning(w));
    }

    setData({ profile, cod, shippingZoneCount: zoneCount, connection });
    setLoading(false);
  }, [activeConnectionId, connections]);

  useEffect(() => {
    if (activeConnectionId !== null && connections !== null) {
      void reload();
    }
  }, [activeConnectionId, connections, reload]);

  if (connections === null) {
    return <LoadingPage label="Loading…" />;
  }

  if (connections.length === 0) {
    return (
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-6 text-2xl font-semibold text-slate-800">
          Store Setup Wizard
        </h1>
        <EmptyState
          title="Add a connection first"
          description="The setup wizard requires a WordPress connection with WooCommerce REST API keys."
          icon={<Globe className="h-10 w-10" />}
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

  const profileStatus: StepStatus = !data?.profile
    ? "unknown"
    : data.profile.checklist.missing > 0
      ? "missing"
      : data.profile.checklist.recommended > 0
        ? "warning"
        : "ok";

  const codStatus: StepStatus = !data?.cod
    ? "unknown"
    : !data.cod.available
      ? "missing"
      : !data.cod.enabled
        ? "warning"
        : "ok";

  const shippingStatus: StepStatus =
    data === null
      ? "unknown"
      : data.shippingZoneCount === 0
        ? "missing"
        : "ok";

  const overallStatus: StepStatus =
    profileStatus === "missing" ||
    codStatus === "missing" ||
    shippingStatus === "missing"
      ? "missing"
      : profileStatus === "warning" || codStatus === "warning"
        ? "warning"
        : profileStatus === "unknown" ||
            codStatus === "unknown" ||
            shippingStatus === "unknown"
          ? "unknown"
          : "ok";

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-800">
            Store Setup Wizard
          </h1>
          <p className="text-sm text-slate-500">
            Review each step and jump to the section that needs attention.
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
            <RefreshCw
              className={`h-4 w-4 ${loading ? "animate-spin" : ""}`}
            />
            Refresh
          </button>
        </div>
      </div>

      {/* Overall status banner */}
      <div
        className={`rounded-lg border p-5 ${
          overallStatus === "ok"
            ? "border-success bg-success-light/30"
            : overallStatus === "warning"
              ? "border-warning bg-warning-light/30"
              : overallStatus === "missing"
                ? "border-danger bg-danger-light/30"
                : "border-surface-border bg-white"
        }`}
      >
        <p className="text-sm font-medium text-slate-800">
          {overallStatus === "ok"
            ? "Your store is fully set up."
            : overallStatus === "warning"
              ? "Store setup is complete, but improvements are recommended."
              : overallStatus === "missing"
                ? "Some required store details are missing."
                : "Setup status could not be fully determined."}
        </p>
        {data?.connection ? (
          <p className="mt-1 font-mono text-xs text-slate-600">
            {data.connection.label} · {data.connection.base_url}
          </p>
        ) : null}
      </div>

      {loading && data === null ? (
        <LoadingPage label="Loading store status…" />
      ) : (
        <div className="space-y-3">
          <SetupStepCard
            number={1}
            title="Store Profile"
            description="Address, currency, units, taxes, and checkout preferences."
            status={profileStatus}
            icon={SettingsIcon}
            detail={
              data?.profile
                ? `${data.profile.checklist.complete} ok · ${data.profile.checklist.recommended} recommended · ${data.profile.checklist.missing} missing`
                : undefined
            }
            warnings={data?.profile?.warnings ?? []}
            ctaLabel="Open Store Settings"
            ctaTo="/wordpress-settings"
          />

          <SetupStepCard
            number={2}
            title="Payment Methods"
            description="Enable Cash on Delivery and configure its title, description, and instructions."
            status={codStatus}
            icon={Wallet}
            detail={
              data?.cod?.available
                ? `COD ${data.cod.enabled ? "enabled" : "disabled"} · ${
                    data.cod.shipping_zones_available
                      ? "shipping zones present"
                      : "no shipping zones"
                  }`
                : undefined
            }
            warnings={data?.cod?.warnings ?? []}
            ctaLabel="Open COD"
            ctaTo="/cod"
          />

          <SetupStepCard
            number={3}
            title="Shipping Zones"
            description="Define where you ship and which methods (flat rate, free shipping, local pickup) are available."
            status={shippingStatus}
            icon={Truck}
            detail={
              data !== null
                ? `${data.shippingZoneCount} zone(s) configured`
                : undefined
            }
            ctaLabel="Open Shipping"
            ctaTo="/shipping"
          />

          <SetupStepCard
            number={4}
            title="Products"
            description="Publish your first WooCommerce product with images, pricing, and SEO metadata."
            status="unknown"
            icon={Package}
            detail="Status not tracked here. Visit the Product Publisher."
            ctaLabel="Open Product Publisher"
            ctaTo="/product-publisher"
          />

          <SetupStepCard
            number={5}
            title="Payments (Other)"
            description="Other payment gateways like bank transfer are read-only in this phase."
            status="unknown"
            icon={CreditCard}
            detail="Not configurable in this phase."
            ctaLabel="View Gateways"
            ctaTo="/wordpress-settings"
          />
        </div>
      )}
    </div>
  );
}