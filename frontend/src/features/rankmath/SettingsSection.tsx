import type { ReactNode } from "react";

interface SettingsSectionProps {
  title: string;
  description: string;
  children: ReactNode;
}

export function SettingsSection({
  title,
  description,
  children,
}: SettingsSectionProps): JSX.Element {
  return (
    <section className="rounded-lg border border-surface-border bg-white p-5">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-slate-800">{title}</h3>
        <p className="text-xs text-slate-500">{description}</p>
      </div>
      <div className="space-y-3">{children}</div>
    </section>
  );
}

interface BooleanToggleProps {
  label: string;
  help?: string;
  value: boolean;
  onChange: (next: boolean) => void;
  disabled?: boolean;
}

export function BooleanToggle({
  label,
  help,
  value,
  onChange,
  disabled = false,
}: BooleanToggleProps): JSX.Element {
  return (
    <label className="flex cursor-pointer items-start gap-3 rounded border border-surface-border px-3 py-2 text-sm hover:bg-surface-muted">
      <input
        type="checkbox"
        checked={value}
        onChange={(e) => onChange(e.target.checked)}
        disabled={disabled}
        className="mt-0.5 h-4 w-4 rounded border-surface-border"
      />
      <span className="flex-1">
        <span className="block font-medium text-slate-800">{label}</span>
        {help ? (
          <span className="block text-xs text-slate-500">{help}</span>
        ) : null}
      </span>
    </label>
  );
}

interface TextInputProps {
  label: string;
  value: string;
  onChange: (next: string) => void;
  placeholder?: string;
  help?: string;
  maxLength?: number;
  disabled?: boolean;
}

export function TextInput({
  label,
  value,
  onChange,
  placeholder,
  help,
  maxLength,
  disabled = false,
}: TextInputProps): JSX.Element {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        maxLength={maxLength}
        disabled={disabled}
        className="block w-full rounded border border-surface-border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-1 disabled:cursor-not-allowed disabled:bg-surface-muted"
      />
      {help ? <p className="mt-1 text-xs text-slate-500">{help}</p> : null}
    </div>
  );
}