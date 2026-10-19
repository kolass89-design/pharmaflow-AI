import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import * as crypto from 'node:crypto';
import { DownloadManager } from '../src/queue';
import { MemoryStore } from '../src/store';
import { startFixtureServer, makeBytes, type FixtureServer } from './fixtureServer';

let server: FixtureServer;
let dir: string;

function sha(buf: Buffer): string {
  return crypto.createHash('sha256').update(buf).digest('hex');
}

async function waitFor(pred: () => boolean, timeoutMs = 20_000, stepMs = 40): Promise<void> {
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutMs) {
    if (pred()) return;
    await new Promise((r) => setTimeout(r, stepMs));
  }
  throw new Error('waitFor timed out');
}

beforeAll(async () => {
  server = await startFixtureServer();
  dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nova-queue-'));
});

afterAll(async () => {
  await server.close();
  fs.rmSync(dir, { recursive: true, force: true });
});

function newManager(maxConcurrent = 2): DownloadManager {
  return new DownloadManager({
    defaultDestDir: dir,
    maxConcurrent,
    allowPrivateNetwork: true,
    store: new MemoryStore(),
  });
}

describe('DownloadManager', () => {
  it('queues, limits concurrency and completes multiple downloads', async () => {
    const m = newManager(2);
    await m.init();
    const sizes = [60_000, 70_000, 80_000];
    for (const n of sizes) await m.add(`${server.base}/file.bin?n=${n}`);
    await waitFor(() => m.list().every((r) => r.state === 'completed'));
    for (const [i, n] of sizes.entries()) {
      const rec = m.list()[i];
      expect(sha(fs.readFileSync(rec.destPath!))).toBe(sha(makeBytes(n)));
    }
    m.shutdown();
  });

  it('warns on duplicate URLs', async () => {
    const m = newManager();
    await m.init();
    const url = `${server.base}/file.bin?n=4321`;
    const first = await m.add(url, { startNow: false });
    const second = await m.add(url, { startNow: false });
    expect(first.duplicate).toBe(false);
    expect(second.duplicate).toBe(true);
    expect(second.existingId).toBe(first.record.id);
    const forced = await m.add(url, { startNow: false, allowDuplicate: true });
    expect(forced.duplicate).toBe(false);
    expect(forced.record.fileName).toMatch(/\(\d+\)\.bin$/); // name de-duplicated on disk too
    m.shutdown();
  });

  it('parses batch lists and reports bad lines', async () => {
    const m = newManager();
    await m.init();
    const { added, errors } = await m.addBatch(
      `${server.base}/file.bin?n=1111\nnot a url\n${server.base}/file.bin?n=2222, ${server.base}/norange.bin?n=3333`,
      { startNow: false },
    );
    expect(added.length).toBe(3);
    expect(errors.length).toBe(1);
    expect(errors[0].line).toBe('not a url');
    m.shutdown();
  });

  it('searches history by name', async () => {
    const m = newManager();
    await m.init();
    await m.add(`${server.base}/named.mp4?n=5000`, { startNow: false });
    await m.add(`${server.base}/file.bin?n=5000`, { startNow: false });
    expect(m.search('named').length).toBe(1);
    expect(m.search('named')[0].category).toBe('video');
    expect(m.search('').length).toBe(2);
    m.shutdown();
  });

  it('reorders the queue', async () => {
    const m = newManager();
    await m.init();
    const a = await m.add(`${server.base}/file.bin?n=101`, { startNow: false });
    const b = await m.add(`${server.base}/file.bin?n=202`, { startNow: false });
    m.move(b.record.id, 'up');
    expect(m.list()[0].id).toBe(b.record.id);
    expect(m.list()[1].id).toBe(a.record.id);
    m.shutdown();
  });

  it('persists and reloads records (crash recovery → paused)', async () => {
    const store = new MemoryStore();
    const m1 = new DownloadManager({ defaultDestDir: dir, allowPrivateNetwork: true, store });
    await m1.init();
    const { record } = await m1.add(`${server.base}/file.bin?n=777`, { startNow: false });
    record.state = 'downloading'; // simulate crash mid-transfer
    await m1.persistNow();
    m1.shutdown();

    const m2 = new DownloadManager({ defaultDestDir: dir, allowPrivateNetwork: true, store });
    await m2.init();
    expect(m2.get(record.id)?.state).toBe('paused');
    m2.shutdown();
  });

  it('cleans up orphaned partial files', async () => {
    const m = newManager();
    await m.init();
    const orphan = path.join(dir, 'orphan.bin.novapart');
    fs.writeFileSync(orphan, 'x');
    const removed = await m.cleanupOrphanPartials();
    expect(removed).toBeGreaterThanOrEqual(1);
    expect(fs.existsSync(orphan)).toBe(false);
    m.shutdown();
  });

  it('rejects unsafe URLs at add-time by default', async () => {
    const m = new DownloadManager({ defaultDestDir: dir, store: new MemoryStore() });
    await m.init();
    await expect(m.add('file:///etc/passwd')).rejects.toThrow(/protocol/i);
    await expect(m.add('http://169.254.169.254/latest/meta-data')).rejects.toThrow(/private|blocked/i);
    m.shutdown();
  });
});
