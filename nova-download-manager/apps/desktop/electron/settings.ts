import * as fs from 'node:fs';
import * as path from 'node:path';
import * as crypto from 'node:crypto';

export type DetectMode = 'off' | 'ask' | 'auto';

export interface NovaSettings {
  destDir: string;
  askDestinationEachTime: boolean;
  maxConcurrent: number;
  theme: 'dark' | 'light';
  /** passive media detection relayed from the browser extension */
  detectMode: DetectMode;
  /** domains where detection is suppressed (hostnames) */
  detectDenyList: string[];
  clipboardWatch: boolean;
  notifications: boolean;
  soundOnComplete: boolean;
  throttleKBps: number | null;
  allowPrivateNetwork: boolean;
  enableSegmented: boolean;
  maxSegments: number;
  keepPartialsOnCancel: boolean;
  bridgeEnabled: boolean;
  bridgePort: number;
  bridgeToken: string;
  closeToTray: boolean;
  categoryDirs: Partial<Record<string, string>>;
}

export function defaultSettings(downloadsDir: string): NovaSettings {
  return {
    destDir: downloadsDir,
    askDestinationEachTime: false,
    maxConcurrent: 3,
    theme: 'dark',
    detectMode: 'ask',
    detectDenyList: [],
    clipboardWatch: false,
    notifications: true,
    soundOnComplete: false,
    throttleKBps: null,
    allowPrivateNetwork: false,
    enableSegmented: true,
    maxSegments: 4,
    keepPartialsOnCancel: false,
    bridgeEnabled: true,
    bridgePort: 47117,
    bridgeToken: crypto.randomBytes(24).toString('hex'),
    closeToTray: false,
    categoryDirs: {},
  };
}

export class SettingsStore {
  private file: string;
  value: NovaSettings;

  constructor(userDataDir: string, downloadsDir: string) {
    this.file = path.join(userDataDir, 'settings.json');
    let loaded: Partial<NovaSettings> = {};
    try {
      loaded = JSON.parse(fs.readFileSync(this.file, 'utf8'));
    } catch {
      /* first run */
    }
    this.value = { ...defaultSettings(downloadsDir), ...loaded };
    if (!this.value.bridgeToken) this.value.bridgeToken = crypto.randomBytes(24).toString('hex');
  }

  save(): void {
    fs.mkdirSync(path.dirname(this.file), { recursive: true });
    const tmp = `${this.file}.tmp`;
    fs.writeFileSync(tmp, JSON.stringify(this.value, null, 2), 'utf8');
    fs.renameSync(tmp, this.file);
  }

  patch(patch: Partial<NovaSettings>): NovaSettings {
    this.value = { ...this.value, ...patch };
    this.save();
    return this.value;
  }
}
