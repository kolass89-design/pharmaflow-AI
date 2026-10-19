import * as http from 'node:http';
import * as crypto from 'node:crypto';
import { validateDownloadUrl, type DownloadManager } from '@nova/core';

/**
 * Local bridge used by the Nova browser extension.
 * Security properties:
 *  - Binds to 127.0.0.1 only (never exposed to the LAN/internet).
 *  - Every mutating request requires the per-install pairing token
 *    (constant-time comparison). The token is shown in Nova's
 *    "Browser integration" screen and pasted into the extension once.
 *  - Only browser-extension origins receive CORS headers, so random
 *    websites cannot even read responses; and without the token they
 *    cannot trigger downloads either.
 *  - Payload size-capped; URLs are re-validated by the core engine.
 */

export interface DetectionPayload {
  kind: 'download' | 'detected';
  url: string;
  fileName?: string;
  pageTitle?: string;
  pageUrl?: string;
  mime?: string;
  size?: number | null;
}

interface BridgeDeps {
  getPort: () => number;
  getToken: () => string;
  isEnabled: () => boolean;
  version: string;
  onPayload: (p: DetectionPayload) => Promise<{ ok: boolean; message: string }>;
}

function tokenMatches(given: string, expected: string): boolean {
  const a = Buffer.from(given);
  const b = Buffer.from(expected);
  if (a.length !== b.length) return false;
  return crypto.timingSafeEqual(a, b);
}

export class BridgeServer {
  private server: http.Server | null = null;
  private deps: BridgeDeps;
  lastSeenAt: number | null = null;
  listeningPort: number | null = null;

  constructor(deps: BridgeDeps) {
    this.deps = deps;
  }

  start(): void {
    if (this.server) return;
    const srv = http.createServer((req, res) => {
      void this.handle(req, res);
    });
    srv.on('error', () => {
      this.listeningPort = null;
    });
    srv.listen(this.deps.getPort(), '127.0.0.1', () => {
      const addr = srv.address();
      this.listeningPort = typeof addr === 'object' && addr ? addr.port : this.deps.getPort();
    });
    this.server = srv;
  }

  stop(): void {
    this.server?.close();
    this.server = null;
    this.listeningPort = null;
  }

  restart(): void {
    this.stop();
    if (this.deps.isEnabled()) this.start();
  }

  private cors(req: http.IncomingMessage, res: http.ServerResponse): boolean {
    const origin = req.headers.origin ?? '';
    if (origin.startsWith('chrome-extension://') || origin.startsWith('moz-extension://') || origin.startsWith('edge-extension://')) {
      res.setHeader('Access-Control-Allow-Origin', origin);
      res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-Nova-Token');
      res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
      return true;
    }
    return false;
  }

  private async handle(req: http.IncomingMessage, res: http.ServerResponse): Promise<void> {
    const send = (code: number, body: unknown) => {
      const json = JSON.stringify(body);
      res.writeHead(code, { 'Content-Type': 'application/json' });
      res.end(json);
    };
    try {
      if (!this.deps.isEnabled()) return send(503, { ok: false, message: 'Bridge disabled in Nova settings' });
      const fromExtension = this.cors(req, res);
      if (req.method === 'OPTIONS') {
        res.writeHead(fromExtension ? 204 : 403);
        res.end();
        return;
      }
      const url = new URL(req.url ?? '/', 'http://127.0.0.1');
      if (req.method === 'GET' && url.pathname === '/ping') {
        // Presence check only — reveals nothing sensitive.
        return send(200, { app: 'Nova Download Manager', version: this.deps.version, bridge: true });
      }
      if (req.method !== 'POST' || (url.pathname !== '/add' && url.pathname !== '/pair-check')) return send(404, { ok: false, message: 'Not found' });
      if (!fromExtension) return send(403, { ok: false, message: 'Origin not allowed' });

      const token = (req.headers['x-nova-token'] as string | undefined) ?? '';
      if (!tokenMatches(token, this.deps.getToken())) {
        return send(401, { ok: false, message: 'Invalid pairing token. Re-pair from Nova → Browser integration.' });
      }
      if (url.pathname === '/pair-check') {
        this.lastSeenAt = Date.now();
        return send(200, { ok: true, message: 'Paired with Nova Download Manager' });
      }

      const body = await new Promise<string>((resolve, reject) => {
        let data = '';
        req.on('data', (c: Buffer) => {
          data += c.toString('utf8');
          if (data.length > 64 * 1024) {
            reject(new Error('Payload too large'));
            req.destroy();
          }
        });
        req.on('end', () => resolve(data));
        req.on('error', reject);
      });

      let payload: DetectionPayload;
      try {
        payload = JSON.parse(body) as DetectionPayload;
      } catch {
        return send(400, { ok: false, message: 'Invalid JSON' });
      }
      if (!payload.url || typeof payload.url !== 'string') return send(400, { ok: false, message: 'Missing url' });
      payload.kind = payload.kind === 'detected' ? 'detected' : 'download';
      this.lastSeenAt = Date.now();
      const result = await this.deps.onPayload(payload);
      return send(result.ok ? 200 : 400, result);
    } catch (e) {
      return send(500, { ok: false, message: e instanceof Error ? e.message : 'Bridge error' });
    }
  }
}

export interface DetectionSettings {
  detectMode: 'off' | 'ask' | 'auto';
  detectDenyList: string[];
  allowPrivateNetwork: boolean;
}

/**
 * Decides what happens to a payload coming from the browser extension.
 * Electron-free so it can be integration-tested in plain Node.
 * - kind 'download' = the user explicitly clicked "Download with Nova".
 * - kind 'detected' = passive detection; behavior follows detectMode.
 */
export function createPayloadHandler(deps: {
  manager: DownloadManager;
  getSettings: () => DetectionSettings;
  onAskDetection: (p: DetectionPayload) => void;
}): (p: DetectionPayload) => Promise<{ ok: boolean; message: string }> {
  return async (p) => {
    const s = deps.getSettings();
    let url: URL;
    try {
      url = validateDownloadUrl(p.url, { allowPrivateNetwork: s.allowPrivateNetwork });
    } catch (e) {
      return { ok: false, message: e instanceof Error ? e.message : 'Invalid URL' };
    }
    if (s.detectDenyList.map((d) => d.toLowerCase()).includes(url.hostname.toLowerCase())) {
      return { ok: false, message: 'Detection is disabled for this domain in Nova settings.' };
    }

    if (p.kind === 'detected') {
      if (s.detectMode === 'off') {
        return { ok: false, message: 'Automatic media detection is off in Nova. Use the extension button to send downloads manually.' };
      }
      if (s.detectMode === 'ask') {
        deps.onAskDetection(p);
        return { ok: true, message: 'Media detected — confirm the download in Nova.' };
      }
      // 'auto' (explicit user opt-in only): fall through and download.
    }

    try {
      const result = await deps.manager.add(url.toString(), {
        source: p.kind === 'detected' ? 'detected' : 'extension',
        pageTitle: p.pageTitle,
        pageUrl: p.pageUrl,
        fileName: p.fileName,
      });
      if (result.duplicate) return { ok: true, message: 'Already in Nova (duplicate skipped).' };
      return { ok: true, message: `Downloading ${result.record.fileName}` };
    } catch (e) {
      return { ok: false, message: e instanceof Error ? e.message : 'Failed to add download' };
    }
  };
}
