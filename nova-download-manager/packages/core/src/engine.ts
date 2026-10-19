import * as http from 'node:http';
import * as https from 'node:https';
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as crypto from 'node:crypto';
import { EventEmitter } from 'node:events';
import { promisify } from 'node:util';
import { Transform, pipeline as pipelineCallback } from 'node:stream';

const pipeline = promisify(pipelineCallback);
import type { DownloadRecord, EngineOptions, ProbeResult, SegmentInfo } from './types';
import { validateDownloadUrl, deriveFileName, sanitizeFileName, redactUrl, UnsafeUrlError } from './urlSafety';

const fsp = fs.promises;
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export class DownloadError extends Error {
  transient: boolean;
  status?: number;
  retryAfterMs?: number;
  constructor(message: string, opts: { transient?: boolean; status?: number; retryAfterMs?: number } = {}) {
    super(message);
    this.name = 'DownloadError';
    this.transient = opts.transient ?? false;
    this.status = opts.status;
    this.retryAfterMs = opts.retryAfterMs;
  }
}

interface HttpResponse {
  res: http.IncomingMessage;
  finalUrl: string;
}

const DEFAULT_UA = 'Nova Download Manager/0.1 (+https://github.com/)';

/** Follows redirects manually so every hop is re-validated. */
function requestFollowingRedirects(
  startUrl: string,
  init: { method: 'GET' | 'HEAD'; headers?: Record<string, string> },
  opts: Required<Pick<EngineOptions, 'allowPrivateNetwork' | 'maxRedirects' | 'userAgent' | 'connectTimeoutMs'>>,
  redirectsLeft: number,
  abortRef: { current?: http.ClientRequest },
): Promise<HttpResponse> {
  return new Promise((resolve, reject) => {
    let url: URL;
    try {
      url = validateDownloadUrl(startUrl, { allowPrivateNetwork: opts.allowPrivateNetwork });
    } catch (e) {
      reject(e);
      return;
    }
    const lib = url.protocol === 'https:' ? https : http;
    const req = lib.request(
      url,
      {
        method: init.method,
        headers: {
          'User-Agent': opts.userAgent,
          Accept: '*/*',
          ...(init.headers ?? {}),
        },
      },
      (res) => {
        const status = res.statusCode ?? 0;
        if ([301, 302, 303, 307, 308].includes(status) && res.headers.location) {
          res.resume();
          if (redirectsLeft <= 0) {
            reject(new DownloadError('Too many redirects', { transient: false }));
            return;
          }
          let next: string;
          try {
            next = new URL(res.headers.location, url).toString();
          } catch {
            reject(new DownloadError('Server sent an invalid redirect location'));
            return;
          }
          requestFollowingRedirects(next, init, opts, redirectsLeft - 1, abortRef).then(resolve, reject);
          return;
        }
        resolve({ res, finalUrl: url.toString() });
      },
    );
    abortRef.current = req;
    req.setTimeout(opts.connectTimeoutMs, () => {
      req.destroy(new DownloadError('Connection timed out', { transient: true }));
    });
    req.on('error', (err: NodeJS.ErrnoException) => {
      if ((err as DownloadError).name === 'DownloadError') reject(err);
      else reject(new DownloadError(friendlyNetError(err), { transient: true }));
    });
    req.end();
  });
}

function friendlyNetError(err: NodeJS.ErrnoException): string {
  switch (err.code) {
    case 'ENOTFOUND':
      return 'Server not found (DNS lookup failed). Check the URL and your connection.';
    case 'ECONNREFUSED':
      return 'Connection refused by the server.';
    case 'ECONNRESET':
      return 'Connection was reset by the server.';
    case 'ETIMEDOUT':
      return 'Connection timed out.';
    case 'ENOSPC':
      return 'Not enough disk space to save this download.';
    case 'EACCES':
    case 'EPERM':
      return 'Permission denied while writing the file. Choose a different folder.';
    case 'CERT_HAS_EXPIRED':
    case 'UNABLE_TO_VERIFY_LEAF_SIGNATURE':
    case 'DEPTH_ZERO_SELF_SIGNED_CERT':
      return 'TLS certificate error — the connection could not be verified as secure.';
    default:
      return err.message || 'Network error';
  }
}

function parseRetryAfter(header: string | string[] | undefined): number | undefined {
  if (!header || Array.isArray(header)) return undefined;
  const secs = parseInt(header, 10);
  if (!Number.isNaN(secs)) return Math.min(secs * 1000, 60_000);
  const date = Date.parse(header);
  if (!Number.isNaN(date)) return Math.max(0, Math.min(date - Date.now(), 60_000));
  return undefined;
}

function statusToError(status: number, headers: http.IncomingHttpHeaders): DownloadError {
  if (status === 401 || status === 403) {
    return new DownloadError(`Access denied by the server (HTTP ${status}). The file may require sign-in; Nova does not bypass authentication.`, { status });
  }
  if (status === 404) return new DownloadError('File not found on the server (HTTP 404). The link may have expired.', { status });
  if (status === 410) return new DownloadError('The file is gone (HTTP 410).', { status });
  if (status === 429) {
    return new DownloadError('The server is rate-limiting requests (HTTP 429).', { status, transient: true, retryAfterMs: parseRetryAfter(headers['retry-after']) });
  }
  if (status >= 500) return new DownloadError(`Server error (HTTP ${status}).`, { status, transient: true, retryAfterMs: parseRetryAfter(headers['retry-after']) });
  return new DownloadError(`Unexpected server response (HTTP ${status}).`, { status });
}

export async function probeUrl(rawUrl: string, opts: EngineOptions = {}): Promise<ProbeResult> {
  const o = normalizeOptions(opts);
  const abortRef: { current?: http.ClientRequest } = {};
  // Try HEAD first.
  try {
    const { res, finalUrl } = await requestFollowingRedirects(rawUrl, { method: 'HEAD' }, o, o.maxRedirects, abortRef);
    const status = res.statusCode ?? 0;
    res.destroy();
    if (status >= 200 && status < 300) {
      const len = parseInt(res.headers['content-length'] ?? '', 10);
      const final = new URL(finalUrl);
      return {
        finalUrl,
        totalBytes: Number.isNaN(len) ? null : len,
        supportsRange: (res.headers['accept-ranges'] ?? '').toLowerCase().includes('bytes'),
        fileName: deriveFileName(final, res.headers['content-disposition'], res.headers['content-type']),
        mime: res.headers['content-type']?.split(';')[0].trim(),
        etag: res.headers.etag,
        lastModified: res.headers['last-modified'],
      };
    }
    if (status === 401 || status === 403 || status === 404 || status === 410) {
      throw statusToError(status, res.headers);
    }
    // fall through to ranged-GET probe for 405/501/etc.
  } catch (e) {
    if (e instanceof UnsafeUrlError) throw e;
    if (e instanceof DownloadError && !e.transient && e.status) throw e;
    // network-level HEAD quirks: try ranged GET probe below
  }
  const { res, finalUrl } = await requestFollowingRedirects(rawUrl, { method: 'GET', headers: { Range: 'bytes=0-0' } }, o, o.maxRedirects, abortRef);
  const status = res.statusCode ?? 0;
  const headers = res.headers;
  res.destroy();
  if (status === 206) {
    const range = headers['content-range'] ?? '';
    const m = range.match(/\/(\d+)\s*$/);
    return {
      finalUrl,
      totalBytes: m ? parseInt(m[1], 10) : null,
      supportsRange: true,
      fileName: deriveFileName(new URL(finalUrl), headers['content-disposition'], headers['content-type']),
      mime: headers['content-type']?.split(';')[0].trim(),
      etag: headers.etag,
      lastModified: headers['last-modified'],
    };
  }
  if (status >= 200 && status < 300) {
    const len = parseInt(headers['content-length'] ?? '', 10);
    return {
      finalUrl,
      totalBytes: Number.isNaN(len) ? null : len,
      supportsRange: false,
      fileName: deriveFileName(new URL(finalUrl), headers['content-disposition'], headers['content-type']),
      mime: headers['content-type']?.split(';')[0].trim(),
      etag: headers.etag,
      lastModified: headers['last-modified'],
    };
  }
  throw statusToError(status, headers);
}

function normalizeOptions(opts: EngineOptions) {
  return {
    allowPrivateNetwork: opts.allowPrivateNetwork ?? false,
    maxRedirects: opts.maxRedirects ?? 10,
    userAgent: opts.userAgent ?? DEFAULT_UA,
    connectTimeoutMs: opts.connectTimeoutMs ?? 20_000,
    segmentThresholdBytes: opts.segmentThresholdBytes ?? 8 * 1024 * 1024,
    maxSegments: Math.max(1, Math.min(opts.maxSegments ?? 4, 8)),
    enableSegmented: opts.enableSegmented ?? true,
    maxAutoRetries: opts.maxAutoRetries ?? 3,
    getThrottleKBps: opts.getThrottleKBps ?? (() => null),
  };
}

interface PartMeta {
  url: string;
  finalUrl?: string;
  totalBytes: number | null;
  etag?: string;
  lastModified?: string;
  segmented: boolean;
  segments?: SegmentInfo[];
}

export declare interface DownloadTask {
  on(event: 'progress', listener: (r: DownloadRecord) => void): this;
  on(event: 'state', listener: (r: DownloadRecord) => void): this;
}

/**
 * A single download. Streaming-only (never buffers a whole file in RAM).
 * Supports pause/resume via HTTP Range when the server allows it, optional
 * segmented parallel download with byte-exact reassembly + size validation,
 * transient-error retries with exponential backoff, and optional throttling.
 */
export class DownloadTask extends EventEmitter {
  readonly record: DownloadRecord;
  private opts: ReturnType<typeof normalizeOptions>;
  private abortRefs = new Set<{ current?: http.ClientRequest }>();
  private activeResponses = new Set<http.IncomingMessage>();
  private running = false;
  private pauseRequested = false;
  private cancelRequested = false;
  private startedAt = 0;
  private samples: { t: number; bytes: number }[] = [];
  private lastProgressEmit = 0;
  private expectedSha256?: string;

  constructor(record: DownloadRecord, opts: EngineOptions = {}) {
    super();
    this.record = record;
    this.opts = normalizeOptions(opts);
  }

  private get partPath(): string {
    return `${this.record.destPath}.novapart`;
  }
  private segmentPartPath(i: number): string {
    return `${this.record.destPath}.novapart.${i}`;
  }
  private get metaPath(): string {
    return `${this.record.destPath}.nova-meta.json`;
  }

  private setState(state: DownloadRecord['state']) {
    this.record.state = state;
    this.record.updatedAt = Date.now();
    if (state !== 'downloading') {
      this.record.speedBps = 0;
      this.record.etaSeconds = null;
    }
    this.emit('state', this.record);
  }

  private emitProgress(force = false) {
    const now = Date.now();
    if (!force && now - this.lastProgressEmit < 150) return;
    this.lastProgressEmit = now;
    this.record.updatedAt = now;
    // rolling 4s speed window
    this.samples.push({ t: now, bytes: this.record.downloadedBytes });
    while (this.samples.length > 2 && now - this.samples[0].t > 4000) this.samples.shift();
    if (this.samples.length >= 2) {
      const first = this.samples[0];
      const dt = (now - first.t) / 1000;
      if (dt > 0) this.record.speedBps = Math.max(0, Math.round((this.record.downloadedBytes - first.bytes) / dt));
    }
    const elapsedTotal = (now - this.startedAt) / 1000;
    if (elapsedTotal > 0) this.record.avgSpeedBps = Math.round(this.record.downloadedBytes / elapsedTotal);
    if (this.record.totalBytes && this.record.speedBps > 0) {
      this.record.etaSeconds = Math.max(0, Math.round((this.record.totalBytes - this.record.downloadedBytes) / this.record.speedBps));
    } else {
      this.record.etaSeconds = null;
    }
    this.emit('progress', this.record);
  }

  async start(): Promise<void> {
    if (this.running) return;
    if (!this.record.destPath) throw new Error('destPath not set');
    this.running = true;
    this.pauseRequested = false;
    this.cancelRequested = false;
    this.startedAt = Date.now();
    this.samples = [];
    try {
      await fsp.mkdir(path.dirname(this.record.destPath), { recursive: true });
      await this.runWithRetries();
    } catch (err) {
      if (this.cancelRequested) {
        this.setState('canceled');
      } else if (this.pauseRequested) {
        this.setState('paused');
      } else {
        this.record.error = err instanceof Error ? err.message : String(err);
        this.setState('failed');
      }
    } finally {
      this.running = false;
      this.emitProgress(true);
      this.emit('state', this.record);
    }
  }

  pause(): void {
    if (!this.running) {
      this.setState('paused');
      return;
    }
    this.pauseRequested = true;
    this.destroyActive();
  }

  async cancel(deletePartial = true): Promise<void> {
    this.cancelRequested = true;
    this.destroyActive();
    if (!this.running) this.setState('canceled');
    if (deletePartial) {
      // small delay so streams release file handles
      await sleep(60);
      await this.cleanupParts().catch(() => undefined);
    }
  }

  private destroyActive() {
    for (const ref of this.abortRefs) ref.current?.destroy(new Error('__nova_aborted__'));
    for (const res of this.activeResponses) res.destroy(new Error('__nova_aborted__'));
  }

  private get aborted(): boolean {
    return this.pauseRequested || this.cancelRequested;
  }

  private async runWithRetries(): Promise<void> {
    let attempt = 0;
    // eslint-disable-next-line no-constant-condition
    while (true) {
      try {
        await this.runOnce();
        return;
      } catch (err) {
        if (this.aborted) throw err;
        const transient = err instanceof DownloadError ? err.transient : false;
        if (!transient || attempt >= this.opts.maxAutoRetries) throw err;
        attempt++;
        this.record.retryCount = attempt;
        const backoff = Math.min(1000 * 2 ** (attempt - 1), 15_000);
        const wait = Math.max(backoff, err instanceof DownloadError ? err.retryAfterMs ?? 0 : 0);
        this.emit('progress', this.record);
        await sleep(wait);
        if (this.aborted) throw err;
      }
    }
  }

  private async runOnce(): Promise<void> {
    this.setState('probing');
    const probe = await probeUrl(this.record.url, this.opts);
    if (this.aborted) throw new Error('__nova_aborted__');
    this.record.finalUrl = probe.finalUrl;
    this.record.totalBytes = probe.totalBytes;
    this.record.supportsRange = probe.supportsRange;
    this.record.mime = probe.mime ?? this.record.mime;
    if (!this.record.fileName || this.record.fileName === 'download') {
      this.record.fileName = sanitizeFileName(probe.fileName);
    }

    const meta = await this.readMeta();
    const sameResource = !!(meta && meta.url === this.record.url &&
      (!meta.etag || !probe.etag || meta.etag === probe.etag) &&
      meta.totalBytes === probe.totalBytes);

    const wantSegmented = this.opts.enableSegmented && probe.supportsRange &&
      probe.totalBytes !== null && probe.totalBytes >= this.opts.segmentThresholdBytes;

    this.setState('downloading');
    if (wantSegmented) {
      await this.downloadSegmented(probe, sameResource ? meta : null);
    } else {
      await this.downloadSingle(probe, sameResource);
    }
    if (this.aborted) throw new Error('__nova_aborted__');
    await this.finalize(probe);
    this.record.completedAt = Date.now();
    this.setState('completed');
  }

  private async downloadSingle(probe: ProbeResult, resumeOk: boolean): Promise<void> {
    this.record.segmented = false;
    let existing = 0;
    if (resumeOk && probe.supportsRange) {
      try {
        existing = (await fsp.stat(this.partPath)).size;
      } catch {
        existing = 0;
      }
      if (probe.totalBytes !== null && existing > probe.totalBytes) {
        await fsp.rm(this.partPath, { force: true });
        existing = 0;
      }
      if (probe.totalBytes !== null && existing === probe.totalBytes && existing > 0) {
        this.record.downloadedBytes = existing;
        return; // already fully downloaded; finalize() will move it
      }
    } else if (!probe.supportsRange) {
      // Server cannot resume: any stale partial must be discarded.
      await fsp.rm(this.partPath, { force: true }).catch(() => undefined);
    }

    const headers: Record<string, string> = {};
    if (existing > 0 && probe.supportsRange) headers.Range = `bytes=${existing}-`;
    await this.saveMeta(probe, false); // before the GET, so no awaits sit between response and piping
    const abortRef: { current?: http.ClientRequest } = {};
    this.abortRefs.add(abortRef);
    try {
      const { res, finalUrl } = await requestFollowingRedirects(this.record.url, { method: 'GET', headers }, this.opts, this.opts.maxRedirects, abortRef);
      this.record.finalUrl = finalUrl;
      const status = res.statusCode ?? 0;
      if (status === 416 && probe.totalBytes !== null && existing === probe.totalBytes) {
        res.destroy();
        this.record.downloadedBytes = existing;
        return;
      }
      if (status !== 200 && status !== 206) {
        const e = statusToError(status, res.headers);
        res.destroy();
        throw e;
      }
      if (status === 200 && existing > 0) {
        // Server ignored our Range request even though it advertised support: restart cleanly.
        existing = 0;
      }
      this.captureExpectedChecksum(res.headers);
      this.record.downloadedBytes = existing;
      await this.pipeToFile(res, this.partPath, existing > 0 && status === 206, (n) => {
        this.record.downloadedBytes += n;
        this.emitProgress();
      });
    } finally {
      this.abortRefs.delete(abortRef);
    }
  }

  private async downloadSegmented(probe: ProbeResult, meta: PartMeta | null): Promise<void> {
    const total = probe.totalBytes as number;
    this.record.segmented = true;
    let segments: SegmentInfo[];
    if (meta?.segmented && meta.segments && meta.segments.length > 0) {
      segments = meta.segments;
      // reconcile with actual part-file sizes
      for (const seg of segments) {
        try {
          const size = (await fsp.stat(this.segmentPartPath(seg.index))).size;
          seg.downloaded = Math.min(size, seg.end - seg.start + 1);
        } catch {
          seg.downloaded = 0;
        }
      }
    } else {
      const n = Math.max(2, Math.min(this.opts.maxSegments, Math.ceil(total / (1024 * 1024))));
      const chunk = Math.floor(total / n);
      segments = Array.from({ length: n }, (_, i) => ({
        index: i,
        start: i * chunk,
        end: i === n - 1 ? total - 1 : (i + 1) * chunk - 1,
        downloaded: 0,
      }));
    }
    this.record.segments = segments;
    this.record.downloadedBytes = segments.reduce((a, s) => a + s.downloaded, 0);
    await this.saveMeta(probe, true);

    const downloadSegment = async (seg: SegmentInfo): Promise<void> => {
      const segLen = seg.end - seg.start + 1;
      if (seg.downloaded >= segLen) return;
      const from = seg.start + seg.downloaded;
      const abortRef: { current?: http.ClientRequest } = {};
      this.abortRefs.add(abortRef);
      try {
        const { res } = await requestFollowingRedirects(
          this.record.url,
          { method: 'GET', headers: { Range: `bytes=${from}-${seg.end}` } },
          this.opts,
          this.opts.maxRedirects,
          abortRef,
        );
        const status = res.statusCode ?? 0;
        if (status !== 206) {
          const e = status === 200
            ? new DownloadError('Server stopped honoring Range requests during segmented download.', { transient: true })
            : statusToError(status, res.headers);
          res.destroy();
          throw e;
        }
        this.captureExpectedChecksum(res.headers);
        await this.pipeToFile(res, this.segmentPartPath(seg.index), seg.downloaded > 0, (n) => {
          seg.downloaded += n;
          this.record.downloadedBytes += n;
          this.emitProgress();
        });
        if (seg.downloaded !== segLen) {
          throw new DownloadError(`Segment ${seg.index} incomplete (${seg.downloaded}/${segLen} bytes).`, { transient: true });
        }
      } finally {
        this.abortRefs.delete(abortRef);
      }
    };

    await Promise.all(segments.map(downloadSegment));
    // Byte-coverage validation: segments must tile [0, total) exactly.
    const sorted = [...segments].sort((a, b) => a.start - b.start);
    let cursor = 0;
    for (const seg of sorted) {
      if (seg.start !== cursor) throw new DownloadError('Segment layout has gaps or overlaps; refusing to assemble a corrupt file.');
      cursor = seg.end + 1;
    }
    if (cursor !== total) throw new DownloadError('Segment layout does not cover the full file; refusing to assemble.');
    // Merge segment parts into the single .novapart file (streamed).
    const out = fs.createWriteStream(this.partPath, { flags: 'w' });
    for (const seg of sorted) {
      await new Promise<void>((resolve, reject) => {
        const rs = fs.createReadStream(this.segmentPartPath(seg.index));
        rs.on('error', reject);
        rs.pipe(out, { end: false });
        rs.on('end', () => resolve());
      });
    }
    await new Promise<void>((resolve, reject) => {
      out.end(() => resolve());
      out.on('error', reject);
    });
    for (const seg of sorted) await fsp.rm(this.segmentPartPath(seg.index), { force: true }).catch(() => undefined);
  }

  private captureExpectedChecksum(headers: http.IncomingHttpHeaders) {
    const v = (headers['x-checksum-sha256'] || headers['x-amz-meta-sha256']) as string | undefined;
    if (v && /^[a-f0-9]{64}$/i.test(v)) this.expectedSha256 = v.toLowerCase();
  }

  private async pipeToFile(
    res: http.IncomingMessage,
    filePath: string,
    append: boolean,
    onBytes: (n: number) => void,
  ): Promise<void> {
    // Race guard: socket may already have died before we got here.
    if (res.destroyed && !res.complete) {
      throw new DownloadError('Connection closed before the download finished', { transient: true });
    }
    this.activeResponses.add(res);
    const ws = fs.createWriteStream(filePath, { flags: append ? 'a' : 'w' });
    const pace = this.makePacer();
    // stream.pipeline: handles backpressure and ERR_STREAM_PREMATURE_CLOSE
    // (server dropping the connection mid-body) reliably — hand-rolled
    // 'data'/'aborted' plumbing can miss events on already-dead streams.
    const counter = new Transform({
      transform: (chunk: Buffer, _enc, cb) => {
        onBytes(chunk.length);
        const waitMs = pace(chunk.length);
        if (waitMs > 0) setTimeout(() => cb(null, chunk), waitMs);
        else cb(null, chunk);
      },
    });
    try {
      await pipeline(res, counter, ws);
    } catch (e) {
      const err = e as NodeJS.ErrnoException;
      if (this.aborted || err.message === '__nova_aborted__') throw new Error('__nova_aborted__');
      if (err.code === 'ENOSPC' || err.code === 'EACCES' || err.code === 'EPERM') {
        throw new DownloadError(friendlyNetError(err));
      }
      if (err.code === 'ERR_STREAM_PREMATURE_CLOSE') {
        throw new DownloadError('Connection closed before the download finished', { transient: true });
      }
      if (err instanceof DownloadError) throw err;
      throw new DownloadError(err.message || 'Download interrupted', { transient: true });
    } finally {
      this.activeResponses.delete(res);
    }
  }

  /** Simple pacing: returns how long to pause the stream to respect the KB/s cap. */
  private makePacer(): (bytes: number) => number {
    let windowBytes = 0;
    let windowStart = Date.now();
    return (bytes: number) => {
      const kbps = this.opts.getThrottleKBps();
      if (!kbps || kbps <= 0) return 0;
      const now = Date.now();
      if (now - windowStart >= 1000) {
        windowStart = now;
        windowBytes = 0;
      }
      windowBytes += bytes;
      const budget = kbps * 1024;
      if (windowBytes <= budget) return 0;
      const over = windowBytes - budget;
      return Math.min(900, Math.ceil((over / budget) * 1000));
    };
  }

  private async finalize(probe: ProbeResult): Promise<void> {
    const stat = await fsp.stat(this.partPath).catch(() => null);
    if (!stat) throw new DownloadError('Downloaded data is missing (partial file not found).', { transient: true });
    if (probe.totalBytes !== null && stat.size !== probe.totalBytes) {
      throw new DownloadError(
        `Incomplete download: received ${stat.size} of ${probe.totalBytes} bytes. The partial file was kept so you can resume.`,
        { transient: true },
      );
    }
    // SHA-256 (recorded always; verified when the server published one).
    const sha = await new Promise<string>((resolve, reject) => {
      const hash = crypto.createHash('sha256');
      const rs = fs.createReadStream(this.partPath);
      rs.on('data', (c) => hash.update(c));
      rs.on('end', () => resolve(hash.digest('hex')));
      rs.on('error', reject);
    });
    this.record.sha256 = sha;
    if (this.expectedSha256 && this.expectedSha256 !== sha) {
      throw new DownloadError('Integrity check failed: the file does not match the SHA-256 checksum published by the server. The corrupt partial file will be discarded on retry.');
    }
    await fsp.rename(this.partPath, this.record.destPath as string).catch(async (e: NodeJS.ErrnoException) => {
      if (e.code === 'EXDEV') {
        await promisify(fs.copyFile)(this.partPath, this.record.destPath as string);
        await fsp.rm(this.partPath, { force: true });
      } else throw e;
    });
    await fsp.rm(this.metaPath, { force: true }).catch(() => undefined);
  }

  private async readMeta(): Promise<PartMeta | null> {
    try {
      const raw = await fsp.readFile(this.metaPath, 'utf8');
      return JSON.parse(raw) as PartMeta;
    } catch {
      return null;
    }
  }

  private async saveMeta(probe: ProbeResult, segmented: boolean): Promise<void> {
    const meta: PartMeta = {
      url: this.record.url,
      finalUrl: probe.finalUrl,
      totalBytes: probe.totalBytes,
      etag: probe.etag,
      lastModified: probe.lastModified,
      segmented,
      segments: segmented ? this.record.segments : undefined,
    };
    await fsp.writeFile(this.metaPath, JSON.stringify(meta), 'utf8').catch(() => undefined);
  }

  private async cleanupParts(): Promise<void> {
    await fsp.rm(this.partPath, { force: true }).catch(() => undefined);
    await fsp.rm(this.metaPath, { force: true }).catch(() => undefined);
    if (this.record.segments) {
      for (const s of this.record.segments) await fsp.rm(this.segmentPartPath(s.index), { force: true }).catch(() => undefined);
    } else {
      for (let i = 0; i < 16; i++) await fsp.rm(this.segmentPartPath(i), { force: true }).catch(() => undefined);
    }
  }
}

export { redactUrl };
