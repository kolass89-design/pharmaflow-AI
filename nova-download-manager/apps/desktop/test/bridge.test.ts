import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import * as http from 'node:http';
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import type { AddressInfo } from 'node:net';
import { DownloadManager, MemoryStore } from '@nova/core';
import { BridgeServer, createPayloadHandler, type DetectionPayload, type DetectionSettings } from '../electron/bridge';

const TOKEN = 'test-token-0123456789abcdef';
const EXT_ORIGIN = 'chrome-extension://abcdefghijklmnopabcdefghijklmnop';
let fixtureBase = '';
let fixture: http.Server;
let dir: string;

const settings: DetectionSettings = { detectMode: 'ask', detectDenyList: [], allowPrivateNetwork: true };
const asked: DetectionPayload[] = [];

let manager: DownloadManager;
let bridge: BridgeServer;
let bridgePort: number;

function makeBytes(n: number): Buffer {
  const b = Buffer.alloc(n);
  for (let i = 0; i < n; i++) b[i] = (i * 13 + 5) % 251;
  return b;
}

beforeAll(async () => {
  dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nova-bridge-'));
  fixture = http.createServer((req, res) => {
    const url = new URL(req.url ?? '/', 'http://x');
    const n = parseInt(url.searchParams.get('n') ?? '60000', 10);
    const body = makeBytes(n);
    const range = (req.headers.range ?? '').match(/bytes=(\d+)-(\d*)/);
    if (range) {
      const start = parseInt(range[1], 10);
      const end = range[2] ? Math.min(parseInt(range[2], 10), n - 1) : n - 1;
      res.writeHead(206, { 'Content-Range': `bytes ${start}-${end}/${n}`, 'Content-Length': String(end - start + 1), 'Accept-Ranges': 'bytes', 'Content-Type': 'video/mp4' });
      if (req.method !== 'HEAD') res.end(body.subarray(start, end + 1)); else res.end();
    } else {
      res.writeHead(200, { 'Content-Length': String(n), 'Accept-Ranges': 'bytes', 'Content-Type': 'video/mp4' });
      if (req.method !== 'HEAD') res.end(body); else res.end();
    }
  });
  await new Promise<void>((r) => fixture.listen(0, '127.0.0.1', () => r()));
  fixtureBase = `http://127.0.0.1:${(fixture.address() as AddressInfo).port}`;

  manager = new DownloadManager({ defaultDestDir: dir, allowPrivateNetwork: true, store: new MemoryStore() });
  await manager.init();

  bridge = new BridgeServer({
    getPort: () => 0, // ephemeral
    getToken: () => TOKEN,
    isEnabled: () => true,
    version: 'test',
    onPayload: createPayloadHandler({ manager, getSettings: () => settings, onAskDetection: (p) => asked.push(p) }),
  });
  // BridgeServer listens on getPort(); 0 = ephemeral — read back the real port.
  bridge.start();
  await new Promise((r) => setTimeout(r, 150));
  bridgePort = bridge.listeningPort as number;
});

afterAll(async () => {
  bridge.stop();
  manager.shutdown();
  await new Promise<void>((r) => fixture.close(() => r()));
  fs.rmSync(dir, { recursive: true, force: true });
});

async function post(payload: unknown, headers: Record<string, string>): Promise<{ status: number; json: any }> {
  const res = await fetch(`http://127.0.0.1:${bridgePort}/add`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify(payload),
  });
  return { status: res.status, json: await res.json().catch(() => ({})) };
}

async function waitFor(pred: () => boolean, ms = 15_000): Promise<void> {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) {
    if (pred()) return;
    await new Promise((r) => setTimeout(r, 40));
  }
  throw new Error('waitFor timeout');
}

describe('BridgeServer', () => {
  it('answers /ping with app identity only', async () => {
    const res = await fetch(`http://127.0.0.1:${bridgePort}/ping`);
    const json = await res.json();
    expect(res.status).toBe(200);
    expect(json.app).toBe('Nova Download Manager');
  });

  it('rejects requests without a valid token', async () => {
    const r = await post({ kind: 'download', url: `${fixtureBase}/a.mp4` }, { Origin: EXT_ORIGIN });
    expect(r.status).toBe(401);
  });

  it('rejects non-extension origins even with a token', async () => {
    const r = await post({ kind: 'download', url: `${fixtureBase}/a.mp4` }, { Origin: 'https://evil.example', 'X-Nova-Token': TOKEN });
    expect(r.status).toBe(403);
  });

  it('explicit "download" from the extension really downloads the file', async () => {
    const r = await post(
      { kind: 'download', url: `${fixtureBase}/movie.mp4?n=60000`, pageTitle: 'Test page' },
      { Origin: EXT_ORIGIN, 'X-Nova-Token': TOKEN },
    );
    expect(r.status).toBe(200);
    expect(r.json.ok).toBe(true);
    await waitFor(() => manager.list().some((x) => x.state === 'completed'));
    const rec = manager.list().find((x) => x.state === 'completed')!;
    expect(rec.category).toBe('video');
    expect(rec.source).toBe('extension');
    expect(fs.existsSync(rec.destPath!)).toBe(true);
    expect(fs.readFileSync(rec.destPath!).equals(makeBytes(60000))).toBe(true);
  });

  it('"detected" with mode=ask does NOT download — it asks the user', async () => {
    const before = manager.list().length;
    const r = await post(
      { kind: 'detected', url: `${fixtureBase}/clip.mp4?n=1000`, fileName: 'clip.mp4' },
      { Origin: EXT_ORIGIN, 'X-Nova-Token': TOKEN },
    );
    expect(r.json.ok).toBe(true);
    expect(manager.list().length).toBe(before);
    expect(asked.some((a) => a.url.includes('clip.mp4'))).toBe(true);
  });

  it('"detected" with mode=off is refused', async () => {
    settings.detectMode = 'off';
    const r = await post(
      { kind: 'detected', url: `${fixtureBase}/x.mp4` },
      { Origin: EXT_ORIGIN, 'X-Nova-Token': TOKEN },
    );
    expect(r.json.ok).toBe(false);
    settings.detectMode = 'ask';
  });

  it('deny-listed domains are refused', async () => {
    settings.detectDenyList = ['127.0.0.1'];
    const r = await post(
      { kind: 'download', url: `${fixtureBase}/y.mp4` },
      { Origin: EXT_ORIGIN, 'X-Nova-Token': TOKEN },
    );
    expect(r.json.ok).toBe(false);
    expect(r.json.message).toMatch(/disabled for this domain/i);
    settings.detectDenyList = [];
  });

  it('blocks private-network URLs when not opted in', async () => {
    const strict = createPayloadHandler({
      manager,
      getSettings: () => ({ detectMode: 'ask', detectDenyList: [], allowPrivateNetwork: false }),
      onAskDetection: () => undefined,
    });
    const res = await strict({ kind: 'download', url: 'http://192.168.1.10/secret.zip' });
    expect(res.ok).toBe(false);
    expect(res.message).toMatch(/private|blocked/i);
  });

  it('blocks non-http URLs from the bridge', async () => {
    const r = await post(
      { kind: 'download', url: 'file:///etc/passwd' },
      { Origin: EXT_ORIGIN, 'X-Nova-Token': TOKEN },
    );
    expect(r.json.ok).toBe(false);
    expect(r.json.message).toMatch(/protocol/i);
  });
});
