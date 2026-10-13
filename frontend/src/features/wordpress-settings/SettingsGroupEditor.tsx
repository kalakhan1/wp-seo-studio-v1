import { useEffect, useMemo, useState } from "react";
import { Save, RotateCcw } from "lucide-react";
import { toast } from "sonner";

import { LoadingPage } from "@/components/feedback/Loading";
import { SettingField } from "@/features/wordpress-settings/SettingField";
import { wcSettingsApi } from "@/services/wcSettingsApi";
import type {
  WCSetting,
  WCSettingValue,
  WCSettingsGroupResponse,
} from "@/types/wcSettings";
import { ApiError } from "@/types/errors";

interface SettingsGroupEditorProps {
  connectionId: number;
  group: string;
  onSaved?: () => void;
}

type ValuesMap = Record<string, WCSettingValue>;

function toValuesMap(settings: WCSetting[]): ValuesMap {
  const out: ValuesMap = {};
  for (const s of settings) {
    out[s.id] = s.value;
  }
  return out;
}

function valuesEqual(
  a: WCSettingValue | undefined,
  b: WCSettingValue | undefined,
): boolean {
  if (a === b) return true;
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false;
    return a.every((x, i) => x === b[i]);
  }
  // Normalise bool and yes/no so "yes" == true and "no" == false.
  const norm = (v: WCSettingValue | undefined): string => {
    if (v === null || v === undefined) return "";
    if (Array.isArray(v)) return v.join("|");
    if (typeof v === "boolean") return v ? "yes" : "no";
    return String(v);
  };
  return norm(a) === norm(b);
}

export function SettingsGroupEditor({
  connectionId,
  group,
  onSaved,
}: SettingsGroupEditorProps): JSX.Element {
  const [data, setData] = useState<WCSettingsGroupResponse | null>(null);
  const [values, setValues] = useState<ValuesMap>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setValues({});
    void (async () => {
      try {
        const res = await wcSettingsApi.getGroup(connectionId, group);
        if (cancelled) return;
        setData(res);
        setValues(toValuesMap(res.settings));
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError) {
          toast.error(`Failed to load settings: ${err.message}`);
        } else {
          toast.error("Failed to load settings.");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [connectionId, group]);

  const dirtyIds = useMemo(() => {
    if (!data) return [] as string[];
    const list: string[] = [];
    for (const s of data.settings) {
      const current = values[s.id];
      if (!valuesEqual(current, s.value)) {
        list.push(s.id);
      }
    }
    return list;
  }, [data, values]);

  const handleReset = (): void => {
    if (data) setValues(toValuesMap(data.settings));
  };

  const handleSave = async (): Promise<void> => {
    if (!data || dirtyIds.length === 0) return;
    setSaving(true);
    let succeeded = 0;
    const failures: string[] = [];

    for (const settingId of dirtyIds) {
      const value = values[settingId] ?? "";
      try {
        await wcSettingsApi.updateSetting(
          connectionId,
          group,
          settingId,
          value,
        );
        succeeded += 1;
      } catch (err) {
        const msg =
          err instanceof ApiError
            ? `${settingId}: ${err.message}`
            : `${settingId}: unknown error`;
        failures.push(msg);
      }
    }

    // Reload the group to reflect actual server state
    try {
      const res = await wcSettingsApi.getGroup(connectionId, group);
      setData(res);
      setValues(toValuesMap(res.settings));
    } catch {
      // ignore; the UI stays with local values
    }

    setSaving(false);

    if (failures.length === 0) {
      toast.success(`Saved ${succeeded} setting(s).`);
      onSaved?.();
    } else if (succeeded === 0) {
      toast.error(`All ${failures.length} updates failed.`);
    } else {
      toast.warning(
        `Saved ${succeeded} setting(s), ${failures.length} failed.`,
      );
    }
  };

  if (!data) {
    return <LoadingPage label={`Loading ${group} settings…`} />;
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between rounded-lg border border-surface-border bg-white px-4 py-3">
        <p className="text-sm text-slate-600">
          {dirtyIds.length === 0
            ? "No unsaved changes."
            : `${dirtyIds.length} unsaved change(s).`}
        </p>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleReset}
            disabled={saving || dirtyIds.length === 0}
            className="inline-flex items-center gap-1.5 rounded border border-surface-border px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-surface-muted disabled:opacity-50"
          >
            <RotateCcw className="h-4 w-4" />
            Reset
          </button>
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={saving || dirtyIds.length === 0}
            className="inline-flex items-center gap-1.5 rounded bg-brand px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
          >
            <Save className="h-4 w-4" />
            {saving ? "Saving…" : "Save changes"}
          </button>
        </div>
      </div>

      <div className="rounded-lg border border-surface-border bg-white p-5">
        {data.settings.length === 0 ? (
          <p className="py-6 text-center text-sm text-slate-500">
            No settings returned for group "{group}".
          </p>
        ) : (
          data.settings.map((s) => (
            <SettingField
              key={s.id}
              setting={s}
              value={values[s.id] ?? s.value}
              onChange={(v) =>
                setValues((prev) => ({ ...prev, [s.id]: v }))
              }
              disabled={saving}
            />
          ))
        )}
      </div>
    </div>
  );
}