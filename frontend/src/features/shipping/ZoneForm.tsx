import { useState } from "react";
import { Loader2, X } from "lucide-react";
import { toast } from "sonner";

import { TextField } from "@/components/inputs/TextField";
import { wcShippingApi } from "@/services/wcShippingApi";
import type { ZoneLocation, ZoneType } from "@/types/wcShipping";
import { ApiError } from "@/types/errors";

interface ZoneFormProps {
  connectionId: number;
  onClose: () => void;
  onSaved: () => void;
}

const LOCATION_TYPES: ZoneType[] = ["country", "state", "postcode", "continent"];

export function ZoneForm({
  connectionId,
  onClose,
  onSaved,
}: ZoneFormProps): JSX.Element {
  const [name, setName] = useState("");
  const [locations, setLocations] = useState<ZoneLocation[]>([]);
  const [codeInput, setCodeInput] = useState("");
  const [typeInput, setTypeInput] = useState<ZoneType>("country");
  const [saving, setSaving] = useState(false);

  const addLocation = (): void => {
    const code = codeInput.trim();
    if (!code) return;
    if (locations.some((l) => l.code === code && l.type === typeInput)) {
      toast.info("Location already added.");
      return;
    }
    setLocations((prev) => [...prev, { code, type: typeInput }]);
    setCodeInput("");
  };

  const removeLocation = (index: number): void => {
    setLocations((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSave = async (): Promise<void> => {
    if (!name.trim()) {
      toast.error("Zone name is required.");
      return;
    }
    setSaving(true);
    try {
      await wcShippingApi.createZone(connectionId, {
        name: name.trim(),
        locations,
      });
      toast.success("Zone created.");
      onSaved();
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Create failed: ${err.message}`);
      } else {
        toast.error("Create failed.");
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-lg bg-white p-5 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-base font-semibold text-slate-800">
            New shipping zone
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-slate-500 hover:bg-surface-muted"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <TextField
          label="Zone name"
          value={name}
          onChange={setName}
          placeholder="Example: Pakistan"
          help="A descriptive name for this shipping zone."
          required
        />

        <div className="mb-2">
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Locations
          </label>
          <div className="mb-2 flex gap-2">
            <select
              value={typeInput}
              onChange={(e) => setTypeInput(e.target.value as ZoneType)}
              className="rounded border border-surface-border bg-white px-3 py-2 text-sm"
            >
              {LOCATION_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <input
              type="text"
              value={codeInput}
              onChange={(e) => setCodeInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addLocation();
                }
              }}
              placeholder={
                typeInput === "country"
                  ? "Example: PK"
                  : typeInput === "state"
                    ? "Example: PK:SD"
                    : "Example: 74200"
              }
              className="flex-1 rounded border border-surface-border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
            />
            <button
              type="button"
              onClick={addLocation}
              className="rounded border border-surface-border px-3 py-2 text-sm font-medium text-slate-700 hover:bg-surface-muted"
            >
              Add
            </button>
          </div>
          <p className="mb-3 text-xs text-slate-500">
            Country codes are 2 letters (PK, US). State codes are
            country:state (PK:SD). Postcodes can include wildcards (74*).
          </p>

          {locations.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {locations.map((loc, i) => (
                <span
                  key={`${loc.type}-${loc.code}-${i}`}
                  className="inline-flex items-center gap-1 rounded-full bg-surface-muted px-3 py-1 text-xs font-medium text-slate-700"
                >
                  <span className="text-slate-400">{loc.type}:</span>
                  <span className="font-mono">{loc.code}</span>
                  <button
                    type="button"
                    onClick={() => removeLocation(i)}
                    className="ml-1 text-slate-400 hover:text-danger"
                    aria-label="Remove"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500">
              No locations yet. You can add them after creating the zone too.
            </p>
          )}
        </div>

        <div className="mt-5 flex justify-end gap-2 border-t border-surface-border pt-4">
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            className="rounded border border-surface-border px-4 py-2 text-sm font-medium text-slate-700 hover:bg-surface-muted disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={saving}
            className="inline-flex items-center gap-2 rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
          >
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Creating…
              </>
            ) : (
              "Create zone"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}