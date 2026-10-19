import { useState } from "react";
import { ChevronDown, Eye, EyeOff } from "lucide-react";
import type { ToolOption } from "@/lib/api";

type Value = string | number | boolean;

interface OptionFieldProps {
  option: ToolOption;
  value: Value;
  onChange: (value: Value) => void;
  disabled?: boolean;
}

const PAGE_PRESETS = [
  { label: "All pages", value: "" },
  { label: "Page 1", value: "1" },
  { label: "Pages 1–3", value: "1-3" },
];

export function OptionField({ option, value, onChange, disabled }: OptionFieldProps) {
  const id = `option-${option.key}`;
  const describedBy = option.help ? `${id}-help` : undefined;
  const [revealed, setRevealed] = useState(false);

  if (option.type === "boolean") {
    const checked = Boolean(value);
    return (
      <div className="flex items-start justify-between gap-4 py-1">
        <div className="min-w-0">
          <label htmlFor={id} className="text-[13px] font-medium text-content">
            {option.label}
          </label>
          {option.help && (
            <p id={describedBy} className="mt-0.5 text-[11.5px] leading-relaxed text-muted">
              {option.help}
            </p>
          )}
        </div>
        <button
          type="button"
          id={id}
          role="switch"
          aria-checked={checked}
          aria-describedby={describedBy}
          disabled={disabled}
          onClick={() => onChange(!checked)}
          className={`relative mt-0.5 inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors ${
            checked ? "bg-brand-600" : "bg-line"
          } disabled:opacity-50`}
        >
          <span
            className={`inline-block h-[18px] w-[18px] transform rounded-full bg-white shadow transition-transform ${
              checked ? "translate-x-[23px]" : "translate-x-[3px]"
            }`}
          />
          <span className="sr-only">{checked ? "Enabled" : "Disabled"}</span>
        </button>
      </div>
    );
  }

  if (option.type === "select") {
    const choices = option.choices ?? [];
    return (
      <div>
        <label htmlFor={id} className="label">
          {option.label}
        </label>
        <div className="relative">
          <select
            id={id}
            className="input appearance-none pr-10"
            value={String(value ?? "")}
            disabled={disabled}
            aria-describedby={describedBy}
            onChange={(event) => onChange(event.target.value)}
          >
            {choices.map((choice) => (
              <option key={choice.value} value={choice.value}>
                {choice.label}
              </option>
            ))}
          </select>
          <ChevronDown
            className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
            aria-hidden="true"
          />
        </div>
        {option.help && (
          <p id={describedBy} className="hint">
            {option.help}
          </p>
        )}
      </div>
    );
  }

  if (option.type === "number") {
    return (
      <div>
        <label htmlFor={id} className="label">
          {option.label}
        </label>
        <input
          id={id}
          type="number"
          inputMode="numeric"
          className="input"
          value={typeof value === "number" ? value : String(value ?? "")}
          min={option.minimum}
          max={option.maximum}
          step={option.step ?? 1}
          disabled={disabled}
          aria-describedby={describedBy}
          onChange={(event) => {
            const raw = event.target.value;
            if (raw === "") {
              onChange(option.minimum ?? 0);
              return;
            }
            onChange(Number(raw));
          }}
        />
        {(option.minimum !== undefined || option.maximum !== undefined) && (
          <p className="hint">
            {option.help ? `${option.help} ` : ""}
            {option.minimum !== undefined && option.maximum !== undefined
              ? `Allowed range: ${option.minimum}–${option.maximum}.`
              : option.maximum !== undefined
                ? `Maximum: ${option.maximum}.`
                : `Minimum: ${option.minimum}.`}
          </p>
        )}
        {!option.help && option.minimum === undefined && option.maximum === undefined && null}
      </div>
    );
  }

  if (option.type === "pages") {
    return (
      <div>
        <label htmlFor={id} className="label">
          {option.label}
          {option.required && <span className="ml-1 text-red-500">*</span>}
        </label>
        <input
          id={id}
          type="text"
          inputMode="text"
          className="input font-medium"
          placeholder={option.placeholder ?? "e.g. 1-3,5,8-"}
          value={String(value ?? "")}
          disabled={disabled}
          required={option.required}
          aria-describedby={describedBy}
          onChange={(event) => onChange(event.target.value)}
        />
        <div className="mt-2 flex flex-wrap gap-1.5">
          {PAGE_PRESETS.map((preset) => (
            <button
              key={preset.label}
              type="button"
              disabled={disabled}
              onClick={() => onChange(preset.value)}
              className="rounded-md border border-line bg-surface px-2 py-1 text-[11px] font-medium text-muted transition-colors hover:border-brand-300 hover:text-content disabled:opacity-50"
            >
              {preset.label}
            </button>
          ))}
        </div>
        {option.help && (
          <p id={describedBy} className="hint">
            {option.help}
          </p>
        )}
      </div>
    );
  }

  if (option.type === "password") {
    return (
      <div>
        <label htmlFor={id} className="label">
          {option.label}
          {option.required && <span className="ml-1 text-red-500">*</span>}
        </label>
        <div className="relative">
          <input
            id={id}
            type={revealed ? "text" : "password"}
            className="input pr-11"
            value={String(value ?? "")}
            placeholder={option.placeholder}
            disabled={disabled}
            required={option.required}
            autoComplete="new-password"
            aria-describedby={describedBy}
            onChange={(event) => onChange(event.target.value)}
          />
          <button
            type="button"
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-muted hover:text-content"
            onClick={() => setRevealed((current) => !current)}
            aria-label={revealed ? "Hide password" : "Show password"}
          >
            {revealed ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
        {option.help && (
          <p id={describedBy} className="hint">
            {option.help}
          </p>
        )}
      </div>
    );
  }

  return (
    <div>
      <label htmlFor={id} className="label">
        {option.label}
        {option.required && <span className="ml-1 text-red-500">*</span>}
      </label>
      <input
        id={id}
        type="text"
        className="input"
        value={String(value ?? "")}
        placeholder={option.placeholder}
        disabled={disabled}
        required={option.required}
        aria-describedby={describedBy}
        onChange={(event) => onChange(event.target.value)}
      />
      {option.help && (
        <p id={describedBy} className="hint">
          {option.help}
        </p>
      )}
    </div>
  );
}
