import { useCallback, useEffect, useState } from "react";
import { Package, RefreshCw } from "lucide-react";
import { toast } from "sonner";

import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingPage } from "@/components/feedback/Loading";
import { StoreProfileCard } from "@/features/wordpress-settings/StoreProfileCard";
import { SettingsGroupEditor } from "@/features/wordpress-settings/SettingsGroupEditor";
import { connectionApi } from "@/services/connectionApi";
import { wcSettingsApi } from "@/services/wcSettingsApi";
import type { Connection } from "@/types/connection";
import type { StoreProfileResponse } from "@/types/wcSettings";
import { ApiError } from "@/types/errors";

const GROUP_LABELS: Record<string, string> = {
  general: "General",
  products: "Products",
  tax: "Tax",
  checkout: "Checkout",
  shipping: "Shipping",
  account: "Accounts & Privacy",
  advanced: "Advanced",
};

export function WCSettingsPage(): JSX.Element {
  const [connections, setConnections] = useState<Connection[] | null>(null);
  const [activeConnectionId, setActiveConnectionId] = useState<number | null>(
    null,
  );
  const [groups, setGroups] = useState<string[]>([]);
  const [activeGroup, setActiveGroup] = useState<string>("general");
  const [profile, setProfile] = useState<StoreProfileResponse | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);

  // Load connections once
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

  // Load groups once
  useEffect(() => {
    void (async () => {
      try {
        const res = await wcSettingsApi.listGroups();
        setGroups(res);
        const firstGroup = res[0];
        if (firstGroup) setActiveGroup(firstGroup);
      } catch {
        setGroups([
          "general",
          "products",
          "tax",
          "checkout",
          "shipping",
          "account",
          "advanced",
        ]);
      }
    })();
  }, []);

  const loadProfile = useCallback(async () => {
    if (activeConnectionId === null) return;
    setProfileLoading(true);
    try {
      const res = await wcSettingsApi.getStoreProfile(activeConnectionId);
      setProfile(res);
    } catch (err) {
      setProfile(null);
      if (err instanceof ApiError) {
        toast.error(`Failed to load store profile: ${err.message}`);
      } else {
        toast.error("Failed to load store profile.");
      }
    } finally {
      setProfileLoading(false);
    }
  }, [activeConnectionId]);

  useEffect(() => {
    if (activeConnectionId !== null) {
      void loadProfile();
    }
  }, [activeConnectionId, loadProfile]);

  if (connections === null) {
    return <LoadingPage label="Loading…" />;
  }

  if (connections.length === 0) {
    return (
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-6 text-2xl font-semibold text-slate-800">
          WooCommerce Settings
        </h1>
        <EmptyState
          title="Add a connection first"
          description="WooCommerce settings require a WordPress connection with REST API keys."
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
          WooCommerce Settings
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
            onClick={() => void loadProfile()}
            disabled={profileLoading}
            className="inline-flex items-center gap-1.5 rounded border border-surface-border px-3 py-2 text-sm font-medium text-slate-700 hover:bg-surface-muted disabled:opacity-50"
          >
            <RefreshCw
              className={`h-4 w-4 ${profileLoading ? "animate-spin" : ""}`}
            />
            Refresh
          </button>
        </div>
      </div>

      {/* Store profile */}
      {profileLoading && !profile ? (
        <LoadingPage label="Loading store profile…" />
      ) : profile ? (
        <StoreProfileCard data={profile} />
      ) : null}

      {/* Group tabs */}
      <div className="rounded-lg border border-surface-border bg-white">
        <div className="flex flex-wrap gap-1 border-b border-surface-border p-2">
          {groups.map((g) => (
            <button
              key={g}
              type="button"
              onClick={() => setActiveGroup(g)}
              className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${
                activeGroup === g
                  ? "bg-brand-light text-brand-dark"
                  : "text-slate-600 hover:bg-surface-muted"
              }`}
            >
              {GROUP_LABELS[g] ?? g}
            </button>
          ))}
        </div>

        <div className="p-5">
          {activeConnectionId !== null ? (
            <SettingsGroupEditor
              key={`${activeConnectionId}-${activeGroup}`}
              connectionId={activeConnectionId}
              group={activeGroup}
              onSaved={() => void loadProfile()}
            />
          ) : null}
        </div>
      </div>
    </div>
  );
}