import { useState } from "react";
import { Loader2, Trash2, X } from "lucide-react";
import { toast } from "sonner";

import { SelectField } from "@/components/inputs/SelectField";
import { TextField } from "@/components/inputs/TextField";
import { wcShippingApi } from "@/services/wcShippingApi";
import type {
  WCAvailableMethod,
  WCShippingMethod,
} from "@/types/wcShipping";
import { ApiError } from "@/types/errors";

interface MethodFormProps {
  connectionId: number;
  zoneId: number;
  availableMethods: WCAvailableMethod[];
  existingMethod: WCShippingMethod | null;
  onClose: () => void;
  onSaved: () => void;
}

export function MethodForm({
  connectionId,
  zoneId,
  availableMethods,
  existingMethod,
  onClose,
  onSaved,
}: MethodFormProps): JSX.Element {
  const isEdit = existingMethod !== null;
  const [methodId, setMethodId] = useState<string>(
    existingMethod?.method_id ?? availableMethods[0]?.id ?? "flat_rate",
  );
  const [title, setTitle] = useState<string>(existingMethod?.title ?? "");
  const [enabled, setEnabled] = useState<boolean>(
    existingMethod?.enabled ?? true,
  );
  const [cost, setCost] = useState<string>(
    extractSettingValue(existingMethod?.settings, "cost"),
  );
  const [minAmount, setMinAmount] = useState<string>(
    extractSettingValue(existingMethod?.settings, "min_amount"),
  );
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleSave = async (): Promise<void> => {
    setSaving(true);
    try {
      const settings: Record<string, unknown> = {};
      if (methodId === "flat_rate" && cost) settings.cost = cost;
      if (methodId === "free_shipping" && minAmount) {
        settings.min_amount = minAmount;
      }

      if (isEdit && existingMethod?.instance_id != null) {
        await wcShippingApi.updateMethod(
          connectionId,
          zoneId,
          existingMethod.instance_id,
          { title, enabled, settings },
        );
        toast.success("Method updated.");
      } else {
        await wcShippingApi.addMethod(connectionId, zoneId, {
          method_id: methodId,
          title: title || undefined,
          enabled,
          settings,
        });
        toast.success("Method added.");
      }
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

  const handleDelete = async (): Promise<void> => {
    if (!existingMethod?.instance_id) return;
    setDeleting(true);
    try {
      await wcShippingApi.deleteMethod(
        connectionId,
        zoneId,
        existingMethod.instance_id,
      );
      toast.success("Method deleted.");
      onSaved();
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Delete failed: ${err.message}`);
      } else {
        toast.error("Delete failed.");
      }
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-lg bg-white p-5 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-base font-semibold text-slate-800">
            {isEdit ? "Edit method" : "Add method"}
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

        {!isEdit ? (
          <SelectField
            label="Method type"
            value={methodId}
            onChange={setMethodId}
            options={availableMethods.map((m) => ({
              value: m.id,
              label: m.title || m.id,
            }))}
            help="Pick from the shipping methods available on this store."
          />
        ) : (
          <div className="mb-4">
            <p className="text-xs uppercase tracking-wide text-slate-400">
              Method type
            </p>
            <p className="font-mono text-sm text-slate-800">
              {existingMethod?.method_id}
            </p>
          </div>
        )}

        <TextField
          label="Title"
          value={title}
          onChange={setTitle}
          placeholder={
            methodId === "flat_rate"
              ? "Example: Flat rate"
              : methodId === "free_shipping"
                ? "Example: Free shipping"
                : "Example: Local pickup"
          }
          help="Shown to the customer at checkout. Leave empty for the default."
        />

        {methodId === "flat_rate" ? (
          <TextField
            label="Cost"
            value={cost}
            onChange={setCost}
            placeholder="Example: 150"
            help="Fixed shipping cost in your store currency."
          />
        ) : null}

        {methodId === "free_shipping" ? (
          <TextField
            label="Minimum order amount"
            value={minAmount}
            onChange={setMinAmount}
            placeholder="Example: 1000"
            help="Free shipping applies when cart total reaches this amount."
          />
        ) : null}

        <label className="mb-4 flex cursor-pointer items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
            className="h-4 w-4 rounded border-surface-border"
          />
          Enabled
        </label>

        <div className="flex justify-between gap-2 border-t border-surface-border pt-4">
          {isEdit ? (
            <button
              type="button"
              onClick={() => void handleDelete()}
              disabled={deleting || saving}
              className="inline-flex items-center gap-1 rounded border border-danger px-3 py-2 text-sm font-medium text-danger hover:bg-danger-light disabled:opacity-50"
            >
              {deleting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
              Delete
            </button>
          ) : (
            <span />
          )}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={saving || deleting}
              className="rounded border border-surface-border px-4 py-2 text-sm font-medium text-slate-700 hover:bg-surface-muted disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => void handleSave()}
              disabled={saving || deleting}
              className="rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
            >
              {saving ? "Saving…" : isEdit ? "Save changes" : "Add method"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function extractSettingValue(
  settings: Record<string, unknown> | undefined,
  key: string,
): string {
  if (!settings) return "";
  const entry = settings[key];
  if (entry && typeof entry === "object" && "value" in entry) {
    const v = (entry as { value?: unknown }).value;
    return v == null ? "" : String(v);
  }
  return "";
}