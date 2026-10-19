export interface NovaExtSettings {
  token: string;
  port: number;
  autoDetect: boolean;
}

export const DEFAULT_SETTINGS: NovaExtSettings = { token: '', port: 47117, autoDetect: false };

export async function getSettings(): Promise<NovaExtSettings> {
  const s = await chrome.storage.local.get(['token', 'port', 'autoDetect']);
  return {
    token: typeof s.token === 'string' ? s.token : '',
    port: typeof s.port === 'number' ? s.port : 47117,
    autoDetect: s.autoDetect === true,
  };
}

export interface BridgeResult { ok: boolean; message: string }

async function post(path: string, payload: unknown, settings: NovaExtSettings): Promise<BridgeResult> {
  try {
    const res = await fetch(`http://127.0.0.1:${settings.port}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Nova-Token': settings.token },
      body: JSON.stringify(payload),
    });
    const json = (await res.json().catch(() => ({}))) as Partial<BridgeResult>;
    return { ok: json.ok === true, message: json.message ?? `HTTP ${res.status}` };
  } catch {
    return { ok: false, message: 'Nova is not running. Start Nova Download Manager and try again.' };
  }
}

export async function ping(settings: NovaExtSettings): Promise<boolean> {
  try {
    const ctrl = new AbortController();
    const to = setTimeout(() => ctrl.abort(), 1800);
    const res = await fetch(`http://127.0.0.1:${settings.port}/ping`, { signal: ctrl.signal });
    clearTimeout(to);
    if (!res.ok) return false;
    const j = (await res.json()) as { app?: string };
    return j.app === 'Nova Download Manager';
  } catch {
    return false;
  }
}

export async function pairCheck(settings: NovaExtSettings): Promise<BridgeResult> {
  return post('/pair-check', {}, settings);
}

export interface SendPayload {
  kind: 'download' | 'detected';
  url: string;
  fileName?: string;
  pageTitle?: string;
  pageUrl?: string;
  mime?: string;
}

export async function sendToNova(payload: SendPayload, settings?: NovaExtSettings): Promise<BridgeResult> {
  const s = settings ?? (await getSettings());
  if (!s.token) return { ok: false, message: 'Not paired yet. Open the extension settings and paste the token from Nova → Browser integration.' };
  return post('/add', payload, s);
}
