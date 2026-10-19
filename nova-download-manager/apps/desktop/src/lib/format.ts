export function formatBytes(n: number | null | undefined): string {
  if (n === null || n === undefined) return 'Unknown size';
  if (n < 1024) return `${n} B`;
  const units = ['KB', 'MB', 'GB', 'TB'];
  let v = n / 1024;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
  return `${v.toFixed(v >= 100 ? 0 : v >= 10 ? 1 : 2)} ${units[i]}`;
}
export function formatSpeed(bps: number): string { return `${formatBytes(bps)}/s`; }
export function formatEta(s: number | null): string {
  if (s === null || !Number.isFinite(s)) return '—';
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m ${s % 60}s`;
  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
}
export function formatTime(sec: number): string {
  if (!Number.isFinite(sec) || sec < 0) sec = 0;
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}
export function timeAgo(ts: number): string {
  const d = Date.now() - ts;
  if (d < 60_000) return 'just now';
  if (d < 3_600_000) return `${Math.floor(d / 60_000)}m ago`;
  if (d < 86_400_000) return `${Math.floor(d / 3_600_000)}h ago`;
  return new Date(ts).toLocaleDateString();
}
export function baseName(p: string): string {
  return p.replace(/\\/g, '/').split('/').pop() ?? p;
}
export const CATEGORY_ICON: Record<string, string> = {
  video: '🎬', audio: '🎵', documents: '📄', archives: '🗜️', images: '🖼️', applications: '💿', other: '📦',
};
export const STATE_LABEL: Record<string, string> = {
  queued: 'Queued', probing: 'Connecting', downloading: 'Downloading', paused: 'Paused',
  completed: 'Completed', failed: 'Failed', canceled: 'Canceled',
};
