import { useEffect, useState } from "react";
import { Loader2, Save } from "lucide-react";
import { toast } from "sonner";

import { TextField } from "@/components/inputs/TextField";
import { TextArea } from "@/components/inputs/TextArea";
import { wcGatewayApi } from "@/services/wcGatewayApi";
import type { CODSettings, CODStatus } from "@/types/wcGateway";
import { ApiError } from "@/types/errors";

interface CODFormProps {
  connectionId: number;
  status: CODStatus | null;
  onSaved: () => void;
  disabled?: boolean;
}

interface FormState {
  enabled: boolean;
  title: string;
  description: string;
  instructions: string;
  enableForVirtual: boolean;
}

const INITIAL: FormState = {
  enabled: false,
  title: "",
  description: "",
  instructions: "",
  enableForVirtual: false,
};

export function CODForm({
  connectionId,
  status,
  onSaved,
  disabled = false,
}: CODFormProps): JSX.Element {
  const [form, setForm] = useState<FormState>(INITIAL);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!status) return;
    setForm({
      enabled: status.enabled,
      title: status.title,
      description: status.description,
      instructions: status.instructions,
      enableForVirtual: status.enable_for_virtual,
    });
  }, [status]);

  const update = <K extends keyof FormState>(key: K, value: FormState[K]): void => {
    setForm((f) => ({ ...f, [key]: value }));
  };

  const dirty =
    !status ||
    form.enabled !== status.enabled ||
    form.title !== status.title ||
    form.description !== status.description ||
    form.instructions !== status.instructions ||
    form.enableForVirtual !== status.enable_for_virtual;

  const handleSave = async (): Promise<void> => {
    setSaving(true);
    try {
      const payload: CODSettings = {
        enabled: form.enabled,
        title: form.title,
        description: form.description,
        instructions: form.instructions,
        enable_for_virtual: form.enableForVirtual,
      };
      await wcGatewayApi.updateCOD(connectionId, payload);
      toast.success("Cash on Delivery settings saved.");
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

  const isDisabled = disabled || saving || !status?.available;

  return (
    <div className="rounded-lg border border-surface-border bg-white p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-base font-semibold text-slate-800">
          Cash on Delivery Configuration
        </h2>
        {!status?.available ? (
          <span className="rounded-full bg-danger-light px-2.5 py-1 text-xs font-medium text-danger">
            Gateway not available
          </span>
        ) : null}
      </div>

      {!status?.available ? (
        <p className="mb-4 rounded border border-danger bg-danger-light/40 px-3 py-2 text-sm text-danger">
          WooCommerce did not return a COD gateway for this store. COD cannot
          be configured here.
        </p>
      ) : null}

      <label className="mb-4 flex cursor-pointer items-center gap-2 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={form.enabled}
          onChange={(e) => update("enabled", e.target.checked)}
          disabled={isDisabled}
          className="h-4 w-4 rounded border-surface-border"
        />
        Enable Cash on Delivery
      </label>

      <TextField
        label="Title"
        value={form.title}
        onChange={(v) => update("title", v)}
        placeholder="Example: Cash on delivery"
        help="Shown next to the COD option at checkout."
        disabled={isDisabled}
        maxLength={200}
      />

      <TextField
        label="Description"
        value={form.description}
        onChange={(v) => update("description", v)}
        placeholder="Example: Pay with cash upon delivery."
        help="Short description shown under the title at checkout."
        disabled={isDisabled}
        maxLength={1000}
      />

      <TextArea
        label="Instructions"
        value={form.instructions}
        onChange={(v) => update("instructions", v)}
        placeholder="Example: Please have exact change ready."
        help="Shown on the thank-you page and order confirmation email."
        rows={3}
        maxLength={2000}
        showCounter
        disabled={isDisabled}
      />

      <label className="mb-4 flex cursor-pointer items-center gap-2 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={form.enableForVirtual}
          onChange={(e) => update("enableForVirtual", e.target.checked)}
          disabled={isDisabled}
          className="h-4 w-4 rounded border-surface-border"
        />
        Allow COD for virtual products
      </label>

      <div className="flex justify-end gap-2 border-t border-surface-border pt-4">
        <button
          type="button"
          onClick={() => status && setForm({
            enabled: status.enabled,
            title: status.title,
            description: status.description,
            instructions: status.instructions,
            enableForVirtual: status.enable_for_virtual,
          })}
          disabled={!dirty || isDisabled}
          className="rounded border border-surface-border px-4 py-2 text-sm font-medium text-slate-700 hover:bg-surface-muted disabled:opacity-50"
        >
          Reset
        </button>
        <button
          type="button"
          onClick={() => void handleSave()}
          disabled={!dirty || isDisabled}
          className="inline-flex items-center gap-2 rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
        >
          {saving ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Saving…
            </>
          ) : (
            <>
              <Save className="h-4 w-4" />
              Save COD settings
            </>
          )}
        </button>
      </div>
    </div>
  );
}