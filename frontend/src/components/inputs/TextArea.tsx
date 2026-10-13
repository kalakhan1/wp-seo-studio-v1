import { useId, type ChangeEvent } from "react";

interface TextAreaProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  help?: string;
  error?: string | null;
  rows?: number;
  disabled?: boolean;
  required?: boolean;
  maxLength?: number;
  showCounter?: boolean;
}

export function TextArea({
  label,
  value,
  onChange,
  placeholder,
  help,
  error,
  rows = 4,
  disabled = false,
  required = false,
  maxLength,
  showCounter = false,
}: TextAreaProps): JSX.Element {
  const id = useId();
  const helpId = `${id}-help`;
  const errorId = `${id}-error`;
  const describedBy = [help ? helpId : null, error ? errorId : null]
    .filter(Boolean)
    .join(" ");

  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>): void => {
    onChange(e.target.value);
  };

  return (
    <div className="mb-4">
      <div className="mb-1 flex items-baseline justify-between">
        <label htmlFor={id} className="block text-sm font-medium text-slate-700">
          {label}
          {required ? <span className="ml-1 text-danger">*</span> : null}
        </label>
        {showCounter && typeof maxLength === "number" ? (
          <span
            className={`text-xs ${
              value.length > maxLength ? "text-danger" : "text-slate-400"
            }`}
          >
            {value.length}/{maxLength}
          </span>
        ) : null}
      </div>
      <textarea
        id={id}
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        rows={rows}
        disabled={disabled}
        maxLength={maxLength}
        aria-invalid={error ? "true" : "false"}
        aria-describedby={describedBy || undefined}
        className={`block w-full rounded border px-3 py-2 text-sm shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-1 disabled:cursor-not-allowed disabled:bg-surface-muted ${
          error ? "border-danger" : "border-surface-border"
        }`}
      />
      {help && !error ? (
        <p id={helpId} className="mt-1 text-xs text-slate-500">
          {help}
        </p>
      ) : null}
      {error ? (
        <p id={errorId} className="mt-1 text-xs text-danger">
          {error}
        </p>
      ) : null}
    </div>
  );
}