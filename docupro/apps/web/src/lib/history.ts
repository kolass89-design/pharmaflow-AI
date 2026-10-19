/** Local conversion history. Metadata only: file names, sizes and outcomes. */

import { readJson, writeJson } from "./storage";
import { loadSettings } from "./settings";

export interface HistoryEntry {
  id: string;
  toolId: string;
  toolTitle: string;
  createdAt: number;
  status: "succeeded" | "failed" | "cancelled";
  files: { name: string; size: number }[];
  artifacts: { name: string; size: number; mediaType: string; url: string }[];
  jobId: string;
  error?: string;
  expiresAt?: number | null;
}

const KEY = "history.v1";
const LIMIT = 60;

export function listHistory(): HistoryEntry[] {
  return readJson<HistoryEntry[]>(KEY, []).sort((a, b) => b.createdAt - a.createdAt);
}

function persist(entries: HistoryEntry[]): void {
  writeJson(KEY, entries.slice(0, LIMIT));
  window.dispatchEvent(new CustomEvent("docupro:history"));
}

export function addHistory(entry: Omit<HistoryEntry, "id" | "createdAt">): void {
  if (!loadSettings().historyEnabled) return;
  const entries = listHistory();
  const record: HistoryEntry = { ...entry, id: crypto.randomUUID(), createdAt: Date.now() };
  persist([record, ...entries.filter((item) => item.jobId !== entry.jobId)]);
}

export function updateHistory(jobId: string, patch: Partial<HistoryEntry>): void {
  const entries = listHistory().map((entry) => (entry.jobId === jobId ? { ...entry, ...patch } : entry));
  persist(entries);
}

export function removeHistory(id: string): void {
  persist(listHistory().filter((entry) => entry.id !== id));
}

export function clearHistory(): void {
  persist([]);
}

export function historyCount(): number {
  return listHistory().length;
}
