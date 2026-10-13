import { useId } from "react";

import type { WCSetting, WCSettingValue } from "@/types/wcSettings";

interface SettingFieldProps {
  setting: WCSetting;
  value: WCSettingValue;
  onChange: (next: WCSettingValue) => void;
  disabled?: boolean;
}

function asString(value: WCSettingValue): string {
  if (value === null || value === undefined) return "";
  if (Array.isArray(value)) return value.join(",");
  return String(value);
}

function asBool(value: WCSettingValue): boolean {
  if (typeof value === "boolean") return value;
  if (typeof value === "string") {
    const v = value.toLowerCase();
    return v === "yes" || v === "true" || v === "1";
  }
  return false;
}

function asList(value: WCSettingValue): string[] {
  if (Array.isArray(value)) return value;
  if (typeof value === "string" && value.length > 0) return [value];
  return [];
}

export function SettingField({
  setting,
  value,
  onChange,
  disabled = false,
}: SettingFieldProps): JSX.Element {
  const id = useId();
  const helpId = `${id}-help`;

  const renderInput = (): JSX.Element => {
    switch (setting.type) {
      case "checkbox":
        return (
          <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-700">
            <input
              id={id}
              type="checkbox"
              checked={asBool(value)}
              onChange={(e) => onChange(e.target.checked)}
              disabled={disabled}
              className="h-4 w-4 rounded border-surface-border"
              aria-describedby={setting.description ? helpId : undefined}
            />
            <span>{asBool(value) ? "Enabled" : "Disabled"}</span>
          </label>
        );

      case "select":
      case "radio":
      case "single_select_page": {
        const strVal = asString(value);
        return (
          <select
            id={id}
            value={strVal}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            aria-describedby={setting.description ? helpId : undefined}
            className="block w-full rounded border border-surface-border bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-1 disabled:cursor-not-allowed disabled:bg-surface-muted"
          >
            {strVal === "" ? <option value="">— not set —</option> : null}
            {Object.entries(setting.options).map(([v, label]) => (
              <option key={v} value={v}>
                {label}
              </option>
            ))}
          </select>
        );
      }

      case "multiselect": {
        const list = asList(value);
        return (
          <div className="flex flex-wrap gap-2">
            {Object.entries(setting.options).length === 0 ? (
              <p className="text-xs text-slate-500">
                No options available for this setting.
              </p>
            ) : (
              Object.entries(setting.options).map(([v, label]) => {
                const checked = list.includes(v);
                return (
                  <label
                    key={v}
                    className={`inline-flex cursor-pointer items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                      checked
                        ? "border-brand bg-brand-light text-brand-dark"
                        : "border-surface-border bg-white text-slate-600 hover:bg-surface-muted"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(e) => {
                        const next = e.target.checked
                          ? [...list, v]
                          : list.filter((x) => x !== v);
                        onChange(next);
                      }}
                      disabled={disabled}
                      className="hidden"
                    />
                    {label}
                  </label>
                );
              })
            )}
          </div>
        );
      }

      case "number":
        return (
          <input
            id={id}
            type="number"
            value={asString(value)}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            aria-describedby={setting.description ? helpId : undefined}
            className="block w-full rounded border border-surface-border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-1 disabled:cursor-not-allowed disabled:bg-surface-muted"
          />
        );

      case "textarea":
        return (
          <textarea
            id={id}
            value={asString(value)}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            rows={3}
            aria-describedby={setting.description ? helpId : undefined}
            className="block w-full rounded border border-surface-border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-1 disabled:cursor-not-allowed disabled:bg-surface-muted"
          />
        );

      case "color":
        return (
          <input
            id={id}
            type="color"
            value={asString(value) || "#000000"}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            className="h-10 w-20 rounded border border-surface-border"
          />
        );

      case "email":
        return (
          <input
            id={id}
            type="email"
            value={asString(value)}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            className="block w-full rounded border border-surface-border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-1 disabled:cursor-not-allowed disabled:bg-surface-muted"
          />
        );

      case "url":
        return (
          <input
            id={id}
            type="url"
            value={asString(value)}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            className="block w-full rounded border border-surface-border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-1 disabled:cursor-not-allowed disabled:bg-surface-muted"
          />
        );

      case "text":
      default:
        return (
          <input
            id={id}
            type="text"
            value={asString(value)}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            aria-describedby={setting.description ? helpId : undefined}
            className="block w-full rounded border border-surface-border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-1 disabled:cursor-not-allowed disabled:bg-surface-muted"
          />
        );
    }
  };

  return (
    <div className="mb-5">
      <label
        htmlFor={id}
        className="mb-1 block text-sm font-medium text-slate-700"
      >
        {setting.label || setting.id}
        <span className="ml-2 font-mono text-[10px] text-slate-400">
          {setting.id}
        </span>
      </label>
      {renderInput()}
      {setting.description ? (
        <p id={helpId} className="mt-1 text-xs text-slate-500">
          {setting.description}
        </p>
      ) : null}
      {setting.tip ? (
        <p className="mt-1 text-xs text-brand-dark">Tip: {setting.tip}</p>
      ) : null}
    </div>
  );
}