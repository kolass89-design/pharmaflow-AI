import { app, BrowserWindow, Tray, Menu, Notification, clipboard, dialog, ipcMain, nativeImage, protocol, shell } from 'electron';
import * as path from 'node:path';
import * as fs from 'node:fs';
import * as crypto from 'node:crypto';
import {
  DownloadManager,
  JsonFileStore,
  probeUrl,
  validateDownloadUrl,
  isExecutableFile,
  formatBytes,
  type DownloadRecord,
  type AddDownloadOptions,
} from '@nova/core';
import { SettingsStore, type NovaSettings } from './settings';
import { BridgeServer, createPayloadHandler, type DetectionPayload } from './bridge';

const APP_URL = process.env.VITE_DEV_SERVER_URL;
const isDev = !!APP_URL;

let win: BrowserWindow | null = null;
let tray: Tray | null = null;
let settings: SettingsStore;
let manager: DownloadManager;
let bridge: BridgeServer;
let clipboardTimer: NodeJS.Timeout | null = null;
let lastClipboard = '';
let quitting = false;

interface PendingDetection extends DetectionPayload {
  id: string;
  at: number;
}
const pendingDetections = new Map<string, PendingDetection>();

// token -> absolute file path, for the nova-media:// streaming protocol
const mediaRegistry = new Map<string, string>();

function send(channel: string, payload: unknown): void {
  if (win && !win.isDestroyed()) win.webContents.send(channel, payload);
}

function engineOpts(): Record<string, unknown> {
  const s = settings.value;
  return {
    allowPrivateNetwork: s.allowPrivateNetwork,
    enableSegmented: s.enableSegmented,
    maxSegments: s.maxSegments,
    keepPartialsOnCancel: s.keepPartialsOnCancel,
    categoryDirs: s.categoryDirs,
    getThrottleKBps: () => settings.value.throttleKBps,
  };
}

function rebuildManager(): DownloadManager {
  const m = new DownloadManager({
    defaultDestDir: settings.value.destDir,
    maxConcurrent: settings.value.maxConcurrent,
    store: new JsonFileStore(path.join(app.getPath('userData'), 'downloads.json')),
    ...engineOpts(),
  } as ConstructorParameters<typeof DownloadManager>[0]);
  m.on('update', (r: DownloadRecord) => {
    send('nova:update', r);
    if (r.state === 'completed' && settings.value.notifications && Notification.isSupported()) {
      new Notification({ title: 'Download complete', body: `${r.fileName} (${formatBytes(r.totalBytes)})`, silent: !settings.value.soundOnComplete }).show();
    }
    if (r.state === 'failed' && settings.value.notifications && Notification.isSupported()) {
      new Notification({ title: 'Download failed', body: `${r.fileName}: ${r.error ?? 'unknown error'}` }).show();
    }
  });
  m.on('removed', (id: string) => send('nova:removed', id));
  return m;
}


function startClipboardWatcher(): void {
  stopClipboardWatcher();
  if (!settings.value.clipboardWatch) return;
  lastClipboard = clipboard.readText();
  clipboardTimer = setInterval(() => {
    const text = clipboard.readText().trim();
    if (!text || text === lastClipboard) return;
    lastClipboard = text;
    if (!/^https?:\/\/\S+$/.test(text) || text.length > 2048) return;
    try {
      validateDownloadUrl(text, { allowPrivateNetwork: settings.value.allowPrivateNetwork });
      send('nova:clipboardUrl', text);
    } catch {
      /* not a downloadable URL — stay silent */
    }
  }, 1500);
}

function stopClipboardWatcher(): void {
  if (clipboardTimer) clearInterval(clipboardTimer);
  clipboardTimer = null;
}

function createWindow(): void {
  win = new BrowserWindow({
    width: 1320,
    height: 860,
    minWidth: 960,
    minHeight: 600,
    title: 'Nova Download Manager',
    autoHideMenuBar: true,
    backgroundColor: '#0b1020',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  if (isDev) void win.loadURL(APP_URL as string);
  else void win.loadFile(path.join(__dirname, '../dist/index.html'));

  win.on('close', (e) => {
    if (!quitting && settings?.value.closeToTray) {
      e.preventDefault();
      win?.hide();
    }
  });
  win.on('closed', () => {
    win = null;
  });
}

function createTray(): void {
  try {
    const iconPath = path.join(app.getAppPath(), 'build', 'icon.png');
    const img = fs.existsSync(iconPath) ? nativeImage.createFromPath(iconPath).resize({ width: 20 }) : nativeImage.createEmpty();
    tray = new Tray(img);
    tray.setToolTip('Nova Download Manager');
    tray.setContextMenu(
      Menu.buildFromTemplate([
        { label: 'Show Nova', click: () => { if (win) { win.show(); win.focus(); } else createWindow(); } },
        { type: 'separator' },
        { label: 'Quit', click: () => { quitting = true; app.quit(); } },
      ]),
    );
    tray.on('click', () => { if (win) { win.show(); win.focus(); } });
  } catch {
    tray = null; // tray is best-effort (e.g. some Linux environments)
  }
}

function registerMediaProtocol(): void {
  protocol.handle('nova-media', async (request) => {
    const token = new URL(request.url).hostname;
    const filePath = mediaRegistry.get(token);
    if (!filePath || !fs.existsSync(filePath)) return new Response('Not found', { status: 404 });
    const stat = fs.statSync(filePath);
    const range = request.headers.get('Range');
    const mime = mimeFor(filePath);
    if (range) {
      const m = range.match(/bytes=(\d*)-(\d*)/);
      if (m) {
        const start = m[1] === '' ? Math.max(0, stat.size - parseInt(m[2], 10)) : parseInt(m[1], 10);
        const end = m[2] === '' || m[1] === '' ? stat.size - 1 : Math.min(parseInt(m[2], 10), stat.size - 1);
        const stream = fs.createReadStream(filePath, { start, end });
        return new Response(stream as unknown as ReadableStream, {
          status: 206,
          headers: {
            'Content-Type': mime,
            'Content-Range': `bytes ${start}-${end}/${stat.size}`,
            'Content-Length': String(end - start + 1),
            'Accept-Ranges': 'bytes',
          },
        });
      }
    }
    const stream = fs.createReadStream(filePath);
    return new Response(stream as unknown as ReadableStream, {
      status: 200,
      headers: { 'Content-Type': mime, 'Content-Length': String(stat.size), 'Accept-Ranges': 'bytes' },
    });
  });
}

function mimeFor(filePath: string): string {
  const ext = path.extname(filePath).toLowerCase();
  const map: Record<string, string> = {
    '.mp4': 'video/mp4', '.m4v': 'video/mp4', '.webm': 'video/webm', '.mov': 'video/quicktime',
    '.mp3': 'audio/mpeg', '.m4a': 'audio/mp4', '.aac': 'audio/aac', '.ogg': 'audio/ogg', '.opus': 'audio/opus', '.wav': 'audio/wav', '.flac': 'audio/flac',
  };
  return map[ext] ?? 'application/octet-stream';
}

function registerIpc(): void {
  ipcMain.handle('nova:list', () => manager.list());
  ipcMain.handle('nova:add', async (_e, url: string, options?: AddDownloadOptions) => {
    if (settings.value.askDestinationEachTime && !options?.destDir && win) {
      const chosen = await dialog.showOpenDialog(win, { properties: ['openDirectory', 'createDirectory'], defaultPath: settings.value.destDir });
      if (!chosen.canceled && chosen.filePaths[0]) options = { ...options, destDir: chosen.filePaths[0] };
    }
    return manager.add(url, options);
  });
  ipcMain.handle('nova:addBatch', (_e, text: string, options?: AddDownloadOptions) => manager.addBatch(text, options));
  ipcMain.handle('nova:probe', (_e, url: string) => probeUrl(url, engineOpts()));
  ipcMain.handle('nova:start', (_e, id: string) => manager.start(id));
  ipcMain.handle('nova:pause', (_e, id: string) => manager.pause(id));
  ipcMain.handle('nova:cancel', (_e, id: string) => manager.cancel(id));
  ipcMain.handle('nova:retry', (_e, id: string) => manager.retry(id));
  ipcMain.handle('nova:restart', (_e, id: string) => manager.restart(id));
  ipcMain.handle('nova:remove', (_e, id: string, deleteFile?: boolean) => manager.remove(id, deleteFile));
  ipcMain.handle('nova:move', (_e, id: string, dir: 'up' | 'down') => manager.move(id, dir));
  ipcMain.handle('nova:clearHistory', () => manager.clearHistory(true));
  ipcMain.handle('nova:cleanupPartials', () => manager.cleanupOrphanPartials());
  ipcMain.handle('nova:openFile', async (_e, id: string) => {
    const r = manager.get(id);
    if (!r?.destPath) return { ok: false, message: 'File not found' };
    if (isExecutableFile(r.fileName)) {
      // Nova never launches executables. Reveal in folder so the user can
      // scan/inspect and decide themselves.
      shell.showItemInFolder(r.destPath);
      return { ok: false, message: 'For your safety, Nova does not run downloaded programs. The file was shown in its folder so you can scan it with your antivirus first.' };
    }
    const err = await shell.openPath(r.destPath);
    return { ok: !err, message: err || 'Opened' };
  });
  ipcMain.handle('nova:showInFolder', (_e, id: string) => {
    const r = manager.get(id);
    const target = r?.destPath && fs.existsSync(r.destPath) ? r.destPath : r ? `${r.destPath}.novapart` : settings.value.destDir;
    shell.showItemInFolder(target as string);
    return true;
  });
  ipcMain.handle('nova:getSettings', () => settings.value);
  ipcMain.handle('nova:saveSettings', async (_e, patch: Partial<NovaSettings>) => {
    const before = { ...settings.value };
    const next = settings.patch(patch);
    manager.setMaxConcurrent(next.maxConcurrent);
    manager.setDefaultDestDir(next.destDir);
    if (before.clipboardWatch !== next.clipboardWatch) startClipboardWatcher();
    if (before.bridgeEnabled !== next.bridgeEnabled || before.bridgePort !== next.bridgePort) bridge.restart();
    if (before.allowPrivateNetwork !== next.allowPrivateNetwork || before.enableSegmented !== next.enableSegmented || before.maxSegments !== next.maxSegments) {
      // Engine options are captured per-task at construction; rebuild manager for future tasks.
      const old = manager;
      manager = rebuildManager();
      await manager.init();
      old.shutdown();
    }
    return next;
  });
  ipcMain.handle('nova:pickFolder', async () => {
    if (!win) return null;
    const r = await dialog.showOpenDialog(win, { properties: ['openDirectory', 'createDirectory'] });
    return r.canceled ? null : r.filePaths[0];
  });
  ipcMain.handle('nova:pickMediaFiles', async () => {
    if (!win) return [];
    const r = await dialog.showOpenDialog(win, {
      properties: ['openFile', 'multiSelections'],
      filters: [{ name: 'Media', extensions: ['mp4', 'webm', 'mov', 'm4v', 'mp3', 'm4a', 'aac', 'ogg', 'opus', 'wav', 'flac'] }],
    });
    return r.canceled ? [] : r.filePaths;
  });
  ipcMain.handle('nova:registerMedia', (_e, filePath: string) => {
    if (!fs.existsSync(filePath)) throw new Error('File not found');
    const token = crypto.createHash('sha256').update(filePath).digest('hex').slice(0, 32);
    mediaRegistry.set(token, filePath);
    return `nova-media://${token}`;
  });
  const playerStatePath = () => path.join(app.getPath('userData'), 'player.json');
  ipcMain.handle('nova:getPlayerState', () => {
    try {
      return JSON.parse(fs.readFileSync(playerStatePath(), 'utf8'));
    } catch {
      return { positions: {}, playlist: [] };
    }
  });
  ipcMain.handle('nova:savePlayerState', (_e, state: Record<string, unknown>) => {
    fs.writeFileSync(playerStatePath(), JSON.stringify(state), 'utf8');
    return true;
  });
  ipcMain.handle('nova:getDetections', () => [...pendingDetections.values()]);
  ipcMain.handle('nova:acceptDetection', async (_e, id: string) => {
    const d = pendingDetections.get(id);
    if (!d) return { ok: false, message: 'Detection expired' };
    pendingDetections.delete(id);
    try {
      const r = await manager.add(d.url, { source: 'detected', pageTitle: d.pageTitle, pageUrl: d.pageUrl, fileName: d.fileName });
      return { ok: true, record: r.record };
    } catch (e) {
      return { ok: false, message: e instanceof Error ? e.message : 'Failed' };
    }
  });
  ipcMain.handle('nova:dismissDetection', (_e, id: string) => pendingDetections.delete(id));
  ipcMain.handle('nova:getBridgeInfo', () => ({
    enabled: settings.value.bridgeEnabled,
    port: bridge.listeningPort ?? settings.value.bridgePort,
    token: settings.value.bridgeToken,
    lastSeenAt: bridge.lastSeenAt,
  }));
  ipcMain.handle('nova:regenerateBridgeToken', () => {
    const token = crypto.randomBytes(24).toString('hex');
    settings.patch({ bridgeToken: token });
    return token;
  });
  ipcMain.handle('nova:openExternal', (_e, url: string) => {
    if (/^https?:\/\//.test(url)) return shell.openExternal(url);
    return false;
  });
}

function handleDeepLink(raw: string): void {
  try {
    const u = new URL(raw);
    if (u.protocol !== 'nova:') return;
    const target = u.searchParams.get('url');
    if (target) {
      validateDownloadUrl(target, { allowPrivateNetwork: settings.value.allowPrivateNetwork });
      void manager.add(target, { source: 'manual' });
    }
  } catch {
    /* ignore malformed deep links */
  }
}

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', (_e, argv) => {
    const link = argv.find((a) => a.startsWith('nova://'));
    if (link) handleDeepLink(link);
    if (win) {
      if (win.isMinimized()) win.restore();
      win.show();
      win.focus();
    }
  });

  protocol.registerSchemesAsPrivileged?.([
    { scheme: 'nova-media', privileges: { stream: true, supportFetchAPI: true, bypassCSP: false } },
  ]);

  void app.whenReady().then(async () => {
    settings = new SettingsStore(app.getPath('userData'), app.getPath('downloads'));
    manager = rebuildManager();
    await manager.init();
    bridge = new BridgeServer({
      getPort: () => settings.value.bridgePort,
      getToken: () => settings.value.bridgeToken,
      isEnabled: () => settings.value.bridgeEnabled,
      version: app.getVersion(),
      onPayload: createPayloadHandler({
        manager,
        getSettings: () => settings.value,
        onAskDetection: (p) => {
          const det: PendingDetection = { ...p, id: crypto.randomUUID(), at: Date.now() };
          for (const [id, existing] of pendingDetections) if (existing.url === p.url) pendingDetections.delete(id);
          pendingDetections.set(det.id, det);
          send('nova:detection', det);
          if (settings.value.notifications && Notification.isSupported()) {
            new Notification({ title: 'Nova detected downloadable media', body: p.fileName ?? p.url, silent: true }).show();
          }
        },
      }),
    });
    if (settings.value.bridgeEnabled) bridge.start();
    registerMediaProtocol();
    registerIpc();
    createWindow();
    createTray();
    startClipboardWatcher();
    if (process.platform === 'win32') app.setAsDefaultProtocolClient?.('nova');
    const deep = process.argv.find((a) => a.startsWith('nova://'));
    if (deep) handleDeepLink(deep);
  });

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
  });

  app.on('before-quit', () => {
    quitting = true;
    stopClipboardWatcher();
    bridge?.stop();
    manager?.shutdown();
  });
}
