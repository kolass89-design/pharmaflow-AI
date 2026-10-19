import { Monitor, Moon, Sun } from "lucide-react";
import type { ThemePreference } from "@/lib/hooks";

const OPTIONS: { value: ThemePreference; label: string; Icon: typeof Sun }[] = [
  { value: "light", label: "Light", Icon: Sun },
  { value: "dark", label: "Dark", Icon: Moon },
  { value: "system", label: "System", Icon: Monitor },
];

export function ThemeToggle({
  preference,
  onChange,
  compact = false,
}: {
  preference: ThemePreference;
  onChange: (value: ThemePreference) => void;
  compact?: boolean;
}) {
  return (
    <div
      className="inline-flex items-center gap-0.5 rounded-xl border border-line bg-raised p-0.5"
      role="radiogroup"
      aria-label="Colour theme"
    >
      {OPTIONS.map(({ value, label, Icon }) => {
        const active = preference === value;
        return (
          <button
            key={value}
            type="button"
            role="radio"
            aria-checked={active}
            title={label}
            aria-label={label}
            onClick={() => onChange(value)}
            className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors ${
              active ? "bg-sunken text-content shadow-sm" : "text-muted hover:text-content"
            }`}
          >
            <Icon className="h-3.5 w-3.5" aria-hidden="true" />
            {!compact && <span>{label}</span>}
          </button>
        );
      })}
    </div>
  );
}
