import type { DownloadRecord, ProbeResult } from '@nova/core';

export type { DownloadRecord, ProbeResult };

export type View =
  | 'overview' | 'all' | 'downloading' | 'queued' | 'completed' | 'failed'
  | 'video' | 'audio' | 'documents' | 'other' | 'player' | 'integration' | 'settings';

export interface NovaSettings {
  destDir: string;
  askDestinationEachTime: boolean;
  maxConcurrent: number;
  theme: 'dark' | 'light';
  detectMode: 'off' | 'ask' | 'auto';
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

export interface Detection {
  id: string;
  kind: string;
  url: string;
  fileName?: string;
  pageTitle?: string;
  pageUrl?: string;
  mime?: string;
  size?: number | null;
  at: number;
}

export interface AddResult { record: DownloadRecord; duplicate: boolean; existingId?: string }

export interface NovaApi {
  listDownloads(): Promise<DownloadRecord[]>;
  add(url: string, options?: Record<string, unknown>): Promise<AddResult>;
  addBatch(text: string, options?: Record<string, unknown>): Promise<{ added: AddResult[]; errors: { line: string; error: string }[] }>;
  probe(url: string): Promise<ProbeResult>;
  start(id: string): Promise<void>;
  pause(id: string): Promise<void>;
  cancel(id: string): Promise<void>;
  retry(id: string): Promise<void>;
  restart(id: string): Promise<void>;
  remove(id: string, deleteFile?: boolean): Promise<void>;
  move(id: string, dir: 'up' | 'down'): Promise<void>;
  clearHistory(): Promise<void>;
  cleanupPartials(): Promise<number>;
  openFile(id: string): Promise<{ ok: boolean; message: string }>;
  showInFolder(id: string): Promise<boolean>;
  getSettings(): Promise<NovaSettings>;
  saveSettings(patch: Partial<NovaSettings>): Promise<NovaSettings>;
  pickFolder(): Promise<string | null>;
  pickMediaFiles(): Promise<string[]>;
  registerMedia(filePath: string): Promise<string>;
  getPlayerState(): Promise<{ positions: Record<string, number>; playlist: string[] }>;
  savePlayerState(state: { positions: Record<string, number>; playlist: string[] }): Promise<boolean>;
  getDetections(): Promise<Detection[]>;
  acceptDetection(id: string): Promise<{ ok: boolean; message?: string }>;
  dismissDetection(id: string): Promise<boolean>;
  getBridgeInfo(): Promise<{ enabled: boolean; port: number; token: string; lastSeenAt: number | null }>;
  regenerateBridgeToken(): Promise<string>;
  openExternal(url: string): Promise<boolean>;
  onUpdate(cb: (r: DownloadRecord) => void): () => void;
  onRemoved(cb: (id: string) => void): () => void;
  onDetection(cb: (d: Detection) => void): () => void;
  onClipboardUrl(cb: (url: string) => void): () => void;
}

import { createMockNova } from './devMock';

const injected = (window as unknown as { nova?: NovaApi }).nova;
export const nova: NovaApi = injected ?? createMockNova();
export const isBrowserPreview = !injected;
