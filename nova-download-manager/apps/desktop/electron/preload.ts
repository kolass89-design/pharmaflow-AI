import { contextBridge, ipcRenderer } from 'electron';

const api = {
  listDownloads: () => ipcRenderer.invoke('nova:list'),
  add: (url: string, options?: Record<string, unknown>) => ipcRenderer.invoke('nova:add', url, options),
  addBatch: (text: string, options?: Record<string, unknown>) => ipcRenderer.invoke('nova:addBatch', text, options),
  probe: (url: string) => ipcRenderer.invoke('nova:probe', url),
  start: (id: string) => ipcRenderer.invoke('nova:start', id),
  pause: (id: string) => ipcRenderer.invoke('nova:pause', id),
  cancel: (id: string) => ipcRenderer.invoke('nova:cancel', id),
  retry: (id: string) => ipcRenderer.invoke('nova:retry', id),
  restart: (id: string) => ipcRenderer.invoke('nova:restart', id),
  remove: (id: string, deleteFile?: boolean) => ipcRenderer.invoke('nova:remove', id, deleteFile),
  move: (id: string, dir: 'up' | 'down') => ipcRenderer.invoke('nova:move', id, dir),
  clearHistory: () => ipcRenderer.invoke('nova:clearHistory'),
  cleanupPartials: () => ipcRenderer.invoke('nova:cleanupPartials'),
  openFile: (id: string) => ipcRenderer.invoke('nova:openFile', id),
  showInFolder: (id: string) => ipcRenderer.invoke('nova:showInFolder', id),
  getSettings: () => ipcRenderer.invoke('nova:getSettings'),
  saveSettings: (patch: Record<string, unknown>) => ipcRenderer.invoke('nova:saveSettings', patch),
  pickFolder: () => ipcRenderer.invoke('nova:pickFolder'),
  pickMediaFiles: () => ipcRenderer.invoke('nova:pickMediaFiles'),
  registerMedia: (filePath: string) => ipcRenderer.invoke('nova:registerMedia', filePath),
  getPlayerState: () => ipcRenderer.invoke('nova:getPlayerState'),
  savePlayerState: (state: Record<string, unknown>) => ipcRenderer.invoke('nova:savePlayerState', state),
  getDetections: () => ipcRenderer.invoke('nova:getDetections'),
  acceptDetection: (id: string) => ipcRenderer.invoke('nova:acceptDetection', id),
  dismissDetection: (id: string) => ipcRenderer.invoke('nova:dismissDetection', id),
  getBridgeInfo: () => ipcRenderer.invoke('nova:getBridgeInfo'),
  regenerateBridgeToken: () => ipcRenderer.invoke('nova:regenerateBridgeToken'),
  openExternal: (url: string) => ipcRenderer.invoke('nova:openExternal', url),
  onUpdate: (cb: (record: unknown) => void) => {
    const listener = (_e: unknown, record: unknown) => cb(record);
    ipcRenderer.on('nova:update', listener);
    return () => ipcRenderer.removeListener('nova:update', listener);
  },
  onRemoved: (cb: (id: string) => void) => {
    const listener = (_e: unknown, id: string) => cb(id);
    ipcRenderer.on('nova:removed', listener);
    return () => ipcRenderer.removeListener('nova:removed', listener);
  },
  onDetection: (cb: (d: unknown) => void) => {
    const listener = (_e: unknown, d: unknown) => cb(d);
    ipcRenderer.on('nova:detection', listener);
    return () => ipcRenderer.removeListener('nova:detection', listener);
  },
  onClipboardUrl: (cb: (url: string) => void) => {
    const listener = (_e: unknown, url: string) => cb(url);
    ipcRenderer.on('nova:clipboardUrl', listener);
    return () => ipcRenderer.removeListener('nova:clipboardUrl', listener);
  },
};

contextBridge.exposeInMainWorld('nova', api);
