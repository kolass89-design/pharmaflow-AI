import type { NovaApi, NovaSettings, DownloadRecord } from './types';

/**
 * Browser-preview shim: used ONLY when the renderer runs outside Electron
 * (no preload bridge) so the real UI can be previewed in a plain browser.
 * The packaged app always receives the real API from preload.ts and this
 * code path is never taken. Demo data is clearly badged in the UI.
 */
export function createMockNova(): NovaApi {
  const now = Date.now();
  let records: DownloadRecord[] = [
    mk({ fileName: 'BigBuckBunny_1080p.mp4', category: 'video', state: 'downloading', totalBytes: 734_003_200, downloadedBytes: 402_110_000, speedBps: 8_400_000, segmented: true, url: 'https://download.example.org/movies/BigBuckBunny_1080p.mp4' }),
    mk({ fileName: 'lecture-12-algorithms.pdf', category: 'documents', state: 'completed', totalBytes: 4_800_000, downloadedBytes: 4_800_000, avgSpeedBps: 2_100_000, url: 'https://university.example.edu/lecture-12.pdf' }),
    mk({ fileName: 'podcast-ep42.mp3', category: 'audio', state: 'completed', totalBytes: 58_000_000, downloadedBytes: 58_000_000, avgSpeedBps: 3_400_000, url: 'https://feeds.example.com/ep42.mp3' }),
    mk({ fileName: 'ubuntu-24.04.iso', category: 'archives', state: 'queued', totalBytes: 5_900_000_000, downloadedBytes: 0, url: 'https://releases.example.org/ubuntu-24.04.iso' }),
    mk({ fileName: 'expired-link.zip', category: 'archives', state: 'failed', totalBytes: null, downloadedBytes: 0, error: 'File not found on the server (HTTP 404). The link may have expired.', url: 'https://files.example.net/expired-link.zip' }),
    mk({ fileName: 'holiday-photo.jpg', category: 'images', state: 'paused', totalBytes: 8_200_000, downloadedBytes: 3_100_000, url: 'https://photos.example.com/holiday.jpg' }),
  ];
  function mk(p: Partial<DownloadRecord>): DownloadRecord {
    return {
      id: Math.random().toString(36).slice(2),
      destDir: 'C:\\Users\\You\\Downloads',
      destPath: `C:\\Users\\You\\Downloads\\${p.fileName}`,
      supportsRange: true, segmented: false, speedBps: 0, avgSpeedBps: 0, etaSeconds: null,
      retryCount: 0, createdAt: now - 3_600_000, updatedAt: now, source: 'manual',
      totalBytes: null, downloadedBytes: 0, state: 'queued', category: 'other', fileName: 'file', url: 'https://example.com',
      ...p,
    } as DownloadRecord;
  }
  let settings: NovaSettings = {
    destDir: 'C:\\Users\\You\\Downloads', askDestinationEachTime: false, maxConcurrent: 3, theme: 'dark',
    detectMode: 'ask', detectDenyList: [], clipboardWatch: false, notifications: true, soundOnComplete: false,
    throttleKBps: null, allowPrivateNetwork: false, enableSegmented: true, maxSegments: 4,
    keepPartialsOnCancel: false, bridgeEnabled: true, bridgePort: 47117, bridgeToken: 'demo-token-paste-into-extension',
    closeToTray: false, categoryDirs: {},
  };
  const subs = new Set<(r: DownloadRecord) => void>();
  const emit = (r: DownloadRecord) => subs.forEach((cb) => cb({ ...r }));
  const tick = setInterval(() => {
    for (const r of records) {
      if (r.state !== 'downloading') continue;
      r.downloadedBytes = Math.min(r.totalBytes ?? Infinity, r.downloadedBytes + r.speedBps * 0.4);
      r.etaSeconds = r.totalBytes ? Math.round((r.totalBytes - r.downloadedBytes) / Math.max(1, r.speedBps)) : null;
      if (r.totalBytes && r.downloadedBytes >= r.totalBytes) { r.state = 'completed'; r.speedBps = 0; r.etaSeconds = null; }
      emit(r);
    }
  }, 400);
  void tick;

  const find = (id: string) => records.find((r) => r.id === id)!;
  const setState = (id: string, state: DownloadRecord['state']) => { const r = find(id); if (r) { r.state = state; if (state === 'downloading') r.speedBps = 5_000_000; emit(r); } };

  const api: NovaApi & { __mock?: boolean } = {
    __mock: true,
    listDownloads: async () => records.map((r) => ({ ...r })),
    add: async (url: string) => {
      const name = url.split('/').pop() || 'download.bin';
      const r = mk({ fileName: name, url, state: 'downloading', totalBytes: 120_000_000, downloadedBytes: 0, speedBps: 6_000_000, category: name.endsWith('.mp4') ? 'video' : 'other' });
      records = [...records, r];
      return { record: { ...r }, duplicate: false };
    },
    addBatch: async (text: string) => {
      const lines = text.split(/\s+/).filter(Boolean);
      return { added: lines.map((l) => ({ record: mk({ url: l, fileName: l.split('/').pop() ?? 'file' }), duplicate: false })), errors: [] };
    },
    probe: async (url: string) => ({ finalUrl: url, totalBytes: 120_000_000, supportsRange: true, fileName: url.split('/').pop() ?? 'file.bin', mime: 'video/mp4' }),
    start: async (id) => setState(id, 'downloading'),
    pause: async (id) => setState(id, 'paused'),
    cancel: async (id) => setState(id, 'canceled'),
    retry: async (id) => setState(id, 'downloading'),
    restart: async (id) => { const r = find(id); if (r) { r.downloadedBytes = 0; setState(id, 'downloading'); } },
    remove: async (id) => { records = records.filter((r) => r.id !== id); },
    move: async () => undefined,
    clearHistory: async () => { records = records.filter((r) => ['downloading', 'queued', 'paused'].includes(r.state)); },
    cleanupPartials: async () => 0,
    openFile: async () => ({ ok: true, message: 'Preview only' }),
    showInFolder: async () => true,
    getSettings: async () => ({ ...settings }),
    saveSettings: async (patch) => { settings = { ...settings, ...patch }; return { ...settings }; },
    pickFolder: async () => 'C:\\Users\\You\\Downloads',
    pickMediaFiles: async () => [],
    registerMedia: async () => '',
    getPlayerState: async () => ({ positions: {}, playlist: [] }),
    savePlayerState: async () => true,
    getDetections: async () => [],
    acceptDetection: async () => ({ ok: true }),
    dismissDetection: async () => true,
    getBridgeInfo: async () => ({ enabled: true, port: 47117, token: settings.bridgeToken, lastSeenAt: null }),
    regenerateBridgeToken: async () => 'demo-token-2',
    openExternal: async () => true,
    onUpdate: (cb) => { subs.add(cb); return () => subs.delete(cb); },
    onRemoved: () => () => undefined,
    onDetection: () => () => undefined,
    onClipboardUrl: () => () => undefined,
  };
  console.warn('[Nova] Running with browser-preview demo data (no Electron bridge found).');
  return api;
}
