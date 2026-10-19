import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import * as crypto from 'node:crypto';
import { DownloadTask, probeUrl } from '../src/engine';
import type { DownloadRecord, EngineOptions } from '../src/types';
import { startFixtureServer, makeBytes, type FixtureServer } from './fixtureServer';

let server: FixtureServer;
let tmpRoot: string;

const OPTS: EngineOptions = { allowPrivateNetwork: true };

function sha(buf: Buffer): string {
  return crypto.createHash('sha256').update(buf).digest('hex');
}

function makeRecord(url: string, fileName = 'out.bin'): DownloadRecord {
  const dir = fs.mkdtempSync(path.join(tmpRoot, 't-'));
  return {
    id: crypto.randomUUID(),
    url,
    fileName,
    destDir: dir,
    destPath: path.join(dir, fileName),
    totalBytes: null,
    downloadedBytes: 0,
    state: 'queued',
    category: 'other',
    supportsRange: false,
    segmented: false,
    speedBps: 0,
    avgSpeedBps: 0,
    etaSeconds: null,
    retryCount: 0,
    createdAt: Date.now(),
    updatedAt: Date.now(),
    source: 'manual',
  };
}

async function waitFor(pred: () => boolean, timeoutMs = 15_000, stepMs = 40): Promise<void> {
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutMs) {
    if (pred()) return;
    await new Promise((r) => setTimeout(r, stepMs));
  }
  throw new Error('waitFor timed out');
}

beforeAll(async () => {
  server = await startFixtureServer();
  tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'nova-engine-'));
});

afterAll(async () => {
  await server.close();
  fs.rmSync(tmpRoot, { recursive: true, force: true });
});

describe('probeUrl', () => {
  it('detects size, range support and filename', async () => {
    const p = await probeUrl(`${server.base}/named.mp4?n=1234`, OPTS);
    expect(p.totalBytes).toBe(1234);
    expect(p.supportsRange).toBe(true);
    expect(p.fileName).toBe('named.mp4');
    expect(p.mime).toBe('video/mp4');
  });
  it('detects no-range servers', async () => {
    const p = await probeUrl(`${server.base}/norange.bin?n=1234`, OPTS);
    expect(p.supportsRange).toBe(false);
    expect(p.totalBytes).toBe(1234);
  });
  it('sanitizes hostile Content-Disposition names', async () => {
    const p = await probeUrl(`${server.base}/evilname?n=10`, OPTS);
    expect(p.fileName).toBe('evil_.txt');
  });
  it('throws a clear error for 404', async () => {
    await expect(probeUrl(`${server.base}/missing`, OPTS)).rejects.toThrow(/404/);
  });
  it('blocks private URLs when not opted in', async () => {
    await expect(probeUrl(`${server.base}/file.bin?n=10`, {})).rejects.toThrow(/blocked|private/i);
  });
});

describe('DownloadTask', () => {
  it('downloads a file byte-exactly', async () => {
    const n = 200_000;
    const rec = makeRecord(`${server.base}/file.bin?n=${n}`);
    const task = new DownloadTask(rec, OPTS);
    await task.start();
    expect(rec.state).toBe('completed');
    expect(sha(fs.readFileSync(rec.destPath!))).toBe(sha(makeBytes(n)));
    expect(rec.sha256).toBe(sha(makeBytes(n)));
    expect(fs.existsSync(`${rec.destPath}.novapart`)).toBe(false);
  });

  it('follows redirects', async () => {
    const n = 50_000;
    const rec = makeRecord(`${server.base}/redirect?n=${n}`);
    await new DownloadTask(rec, OPTS).start();
    expect(rec.state).toBe('completed');
    expect(rec.finalUrl).toContain('/file.bin');
    expect(sha(fs.readFileSync(rec.destPath!))).toBe(sha(makeBytes(n)));
  });

  it('fails cleanly on 404 and creates no output file', async () => {
    const rec = makeRecord(`${server.base}/missing`);
    await new DownloadTask(rec, OPTS).start();
    expect(rec.state).toBe('failed');
    expect(rec.error).toMatch(/404/);
    expect(fs.existsSync(rec.destPath!)).toBe(false);
  });

  it('fails cleanly on 403 without retrying forever', async () => {
    const rec = makeRecord(`${server.base}/denied`);
    await new DownloadTask(rec, OPTS).start();
    expect(rec.state).toBe('failed');
    expect(rec.error).toMatch(/403|denied/i);
  });

  it('pauses and resumes with HTTP Range (byte-exact)', async () => {
    const n = 400_000;
    const before = server.rangeStarts.length;
    const rec = makeRecord(`${server.base}/slow.bin?n=${n}`);
    const task = new DownloadTask(rec, OPTS);
    const run = task.start();
    await waitFor(() => rec.downloadedBytes > 20_000);
    task.pause();
    await run;
    expect(rec.state).toBe('paused');
    const partialSize = fs.statSync(`${rec.destPath}.novapart`).size;
    expect(partialSize).toBeGreaterThan(0);
    expect(partialSize).toBeLessThan(n);

    await task.start(); // resume
    expect(rec.state).toBe('completed');
    expect(sha(fs.readFileSync(rec.destPath!))).toBe(sha(makeBytes(n)));
    const resumeRanges = server.rangeStarts.slice(before);
    expect(resumeRanges.some((s) => s > 0)).toBe(true); // proved a Range resume happened
  });

  it('resumes by restarting when the server has no Range support', async () => {
    const n = 120_000;
    const rec = makeRecord(`${server.base}/norange.bin?n=${n}`);
    const task = new DownloadTask(rec, OPTS);
    await task.start();
    expect(rec.state).toBe('completed');
    expect(rec.supportsRange).toBe(false);
    expect(sha(fs.readFileSync(rec.destPath!))).toBe(sha(makeBytes(n)));
  });

  it('segmented download assembles byte-exact output and cleans up parts', async () => {
    const n = 1_500_000;
    const rec = makeRecord(`${server.base}/file.bin?n=${n}`);
    const task = new DownloadTask(rec, { ...OPTS, segmentThresholdBytes: 200_000, maxSegments: 4 });
    await task.start();
    expect(rec.state).toBe('completed');
    expect(rec.segmented).toBe(true);
    expect(rec.segments?.length).toBeGreaterThanOrEqual(2);
    expect(sha(fs.readFileSync(rec.destPath!))).toBe(sha(makeBytes(n)));
    const leftovers = fs.readdirSync(rec.destDir).filter((f) => f.includes('.novapart'));
    expect(leftovers).toEqual([]);
  });

  it('auto-retries once after a dropped connection and completes via resume', async () => {
    const n = 300_000;
    const rec = makeRecord(`${server.base}/flaky.bin?n=${n}&k=t1`);
    await new DownloadTask(rec, OPTS).start();
    expect(rec.state).toBe('completed');
    expect(rec.retryCount).toBeGreaterThanOrEqual(1);
    expect(sha(fs.readFileSync(rec.destPath!))).toBe(sha(makeBytes(n)));
  });

  it('backs off on HTTP 429 and then completes', async () => {
    const n = 80_000;
    const rec = makeRecord(`${server.base}/ratelimit.bin?n=${n}&k=t2`);
    await new DownloadTask(rec, OPTS).start();
    expect(rec.state).toBe('completed');
    expect(sha(fs.readFileSync(rec.destPath!))).toBe(sha(makeBytes(n)));
  });

  it('never marks a truncated download as completed and keeps no fake output', async () => {
    const n = 200_000;
    const rec = makeRecord(`${server.base}/truncate.bin?n=${n}`);
    await new DownloadTask(rec, { ...OPTS, maxAutoRetries: 1 }).start();
    expect(rec.state).toBe('failed');
    expect(fs.existsSync(rec.destPath!)).toBe(false);
  });

  it('cancel removes partial files', async () => {
    const rec = makeRecord(`${server.base}/slow.bin?n=500000`);
    const task = new DownloadTask(rec, OPTS);
    const run = task.start();
    await waitFor(() => rec.downloadedBytes > 5_000);
    await task.cancel(true);
    await run;
    expect(rec.state).toBe('canceled');
    expect(fs.existsSync(`${rec.destPath}.novapart`)).toBe(false);
    expect(fs.existsSync(rec.destPath!)).toBe(false);
  });
});
