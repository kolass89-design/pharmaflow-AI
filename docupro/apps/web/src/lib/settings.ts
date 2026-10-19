/** User preferences persisted locally (never sent to the server). */

import { readJson, writeJson } from "./storage";

export interface AppSettings {
  historyEnabled: boolean;
  defaultDpi: number;
  confirmBeforeLeaving: boolean;
}

const KEY = "settings.v1";

export const DEFAULT_SETTINGS: AppSettings = {
  historyEnabled: true,
  defaultDpi: 150,
  confirmBeforeLeaving: true,
};

export function loadSettings(): AppSettings {
  const stored = readJson<Partial<AppSettings>>(KEY, {});
  return { ...DEFAULT_SETTINGS, ...stored };
}

export function saveSettings(settings: AppSettings): void {
  writeJson(KEY, settings);
  window.dispatchEvent(new CustomEvent("docupro:settings", { detail: settings }));
}
