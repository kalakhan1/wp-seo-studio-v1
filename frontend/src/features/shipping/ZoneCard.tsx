import { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  Plus,
  Trash2,
} from "lucide-react";

import { MethodForm } from "@/features/shipping/MethodForm";
import type {
  WCAvailableMethod,
  WCShippingMethod,
  WCShippingZoneDetail,
} from "@/types/wcShipping";

interface ZoneCardProps {
  detail: WCShippingZoneDetail;
  availableMethods: WCAvailableMethod[];
  connectionId: number;
  onChanged: () => void;
  onDelete: (zoneId: number) => void;
}

export function ZoneCard({
  detail,
  availableMethods,
  connectionId,
  onChanged,
  onDelete,
}: ZoneCardProps): JSX.Element {
  const [expanded, setExpanded] = useState(false);
  const [showMethodForm, setShowMethodForm] = useState(false);
  const [editingMethod, setEditingMethod] = useState<WCShippingMethod | null>(
    null,
  );

  const zone = detail.zone;

  return (
    <div className="rounded-lg border border-surface-border bg-white">
      <div className="flex items-center gap-3 p-4">
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="rounded p-1 text-slate-500 hover:bg-surface-muted"
          aria-label={expanded ? "Collapse" : "Expand"}
        >
          {expanded ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </button>
        <div className="flex-1">
          <h3 className="font-semibold text-slate-800">{zone.name}</h3>
          <p className="text-xs text-slate-500">
            Zone #{zone.id} · {detail.locations.length} location(s) ·{" "}
            {detail.methods.length} method(s)
          </p>
        </div>
        <button
          type="button"
          onClick={() => onDelete(zone.id)}
          className="inline-flex items-center gap-1 rounded border border-danger px-3 py-1.5 text-xs font-medium text-danger hover:bg-danger-light"
        >
          <Trash2 className="h-3 w-3" />
          Delete
        </button>
      </div>

      {expanded ? (
        <div className="border-t border-surface-border p-4">
          {/* Locations */}
          <div className="mb-6">
            <h4 className="mb-2 text-sm font-semibold text-slate-700">
              Locations
            </h4>
            {detail.locations.length === 0 ? (
              <p className="text-xs text-slate-500">
                No locations assigned. This zone will never match.
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {detail.locations.map((loc, i) => (
                  <span
                    key={`${loc.type}-${loc.code}-${i}`}
                    className="inline-flex items-center gap-1 rounded-full bg-surface-muted px-3 py-1 text-xs font-medium text-slate-700"
                  >
                    <span className="text-slate-400">{loc.type}:</span>
                    <span className="font-mono">{loc.code}</span>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Methods */}
          <div>
            <div className="mb-2 flex items-center justify-between">
              <h4 className="text-sm font-semibold text-slate-700">Methods</h4>
              <button
                type="button"
                onClick={() => {
                  setEditingMethod(null);
                  setShowMethodForm(true);
                }}
                className="inline-flex items-center gap-1 rounded border border-surface-border px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-surface-muted"
              >
                <Plus className="h-3 w-3" />
                Add method
              </button>
            </div>

            {detail.methods.length === 0 ? (
              <p className="text-xs text-slate-500">
                No methods in this zone. Customers cannot check out.
              </p>
            ) : (
              <ul className="divide-y divide-surface-border rounded border border-surface-border">
                {detail.methods.map((m) => (
                  <li
                    key={m.instance_id ?? m.id ?? 0}
                    className="flex items-center gap-3 px-3 py-2 text-sm"
                  >
                    <span
                      className={`inline-block h-2 w-2 rounded-full ${
                        m.enabled ? "bg-success" : "bg-slate-300"
                      }`}
                    />
                    <div className="flex-1">
                      <p className="font-medium text-slate-800">
                        {m.title || m.method_title}
                      </p>
                      <p className="text-xs text-slate-500">
                        <span className="font-mono">{m.method_id}</span>
                        {m.method_description ? ` · ${m.method_description}` : ""}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setEditingMethod(m);
                        setShowMethodForm(true);
                      }}
                      className="rounded border border-surface-border px-2 py-1 text-xs font-medium text-slate-600 hover:bg-surface-muted"
                    >
                      Edit
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      ) : null}

      {showMethodForm ? (
        <MethodForm
          connectionId={connectionId}
          zoneId={zone.id}
          availableMethods={availableMethods}
          existingMethod={editingMethod}
          onClose={() => {
            setShowMethodForm(false);
            setEditingMethod(null);
          }}
          onSaved={() => {
            setShowMethodForm(false);
            setEditingMethod(null);
            onChanged();
          }}
        />
      ) : null}
    </div>
  );
}