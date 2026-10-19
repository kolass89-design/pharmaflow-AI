/** Human friendly formatting helpers (locale aware, no dependencies). */

const BYTE_UNITS = ["B", "KB", "MB", "GB"];

export function formatBytes(bytes: number | null | undefined, fractionDigits = 0): string {
  if (!bytes || bytes < 0) return "0 B";
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < BYTE_UNITS.length - 1) {
    value /= 1024;
    unit += 1;
  }
  const digits = unit === 0 ? 0 : value >= 100 ? 0 : fractionDigits;
  return `${value.toFixed(digits)} ${BYTE_UNITS[unit]}`;
}

export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return "—";
  if (seconds < 1) return "less than a second";
  if (seconds < 60) return `${Math.round(seconds)} seconds`;
  const minutes = Math.floor(seconds / 60);
  const rest = Math.round(seconds % 60);
  if (minutes < 60) return rest ? `${minutes} min ${rest} s` : `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  return `${hours} h ${minutes % 60} min`;
}

export function formatMinutes(minutes: number): string {
  return minutes >= 60 ? formatDuration(minutes * 60) : `${minutes} minutes`;
}

export function formatDateTime(timestamp: number | string | Date): string {
  const date = typeof timestamp === "number" ? new Date(timestamp * 1000) : new Date(timestamp);
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function formatRelative(timestampMs: number): string {
  const diffSeconds = Math.round((timestampMs - Date.now()) / 1000);
  const formatter = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });
  const thresholds: [Intl.RelativeTimeFormatUnit, number][] = [
    ["second", 60],
    ["minute", 60],
    ["hour", 24],
    ["day", 7],
    ["week", 4.35],
    ["month", 12],
    ["year", Number.POSITIVE_INFINITY],
  ];
  let value = diffSeconds;
  for (const [unit, limit] of thresholds) {
    if (Math.abs(value) < limit) return formatter.format(Math.round(value), unit);
    value /= limit;
  }
  return formatter.format(Math.round(value), "year");
}

export function extensionOf(name: string): string {
  const parts = name.split(".");
  return parts.length > 1 ? (parts.pop() as string).toLowerCase() : "";
}

export function fileTypeLabel(file: File): string {
  const ext = extensionOf(file.name);
  return ext ? ext.toUpperCase() : "FILE";
}

export function truncate(value: string, max = 42): string {
  if (value.length <= max) return value;
  const head = Math.ceil((max - 1) / 2);
  const tail = Math.floor((max - 1) / 2);
  return `${value.slice(0, head)}…${value.slice(value.length - tail)}`;
}

export function pluralize(count: number, singular: string, plural = `${singular}s`): string {
  return count === 1 ? singular : plural;
}
