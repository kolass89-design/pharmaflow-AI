import * as fs from 'node:fs';
import * as path from 'node:path';
import * as crypto from 'node:crypto';
import { EventEmitter } from 'node:events';
import type { AddDownloadOptions, DownloadRecord, EngineOptions } from './types';
import { DownloadTask, probeUrl } from './engine';
import { validateDownloadUrl, sanitizeFileName, deduplicatedFileName, deriveFileName } from './urlSafety';
import { categorize } from './categories';
import type { NovaStore } from './store';
import { MemoryStore } from './store';

export interface ManagerOptions extends EngineOptions {
  defaultDestDir: string;
  maxConcurrent?: number;
  store?: NovaStore;
  /** per-category destination folders, e.g. { video: 'D:\\Videos' } */
  categoryDirs?: Partial<Record<string, string>>;
  /** keep .novapart files after cancel (default false = clean up) */
  keepPartialsOnCancel?: boolean;
}

export interface AddResult {
  record: DownloadRecord;
  duplicate: boolean;
  existingId?: string;
}

const ACTIVE_STATES = new Set(['queued', 'probing', 'downloading', 'paused']);

/**
 * Queue + history manager. Owns concurrency limits, ordering, scheduling,
 * deduplication and persistence; DownloadTask owns the transfer itself.
 */
export class DownloadManager extends EventEmitter {
  private records = new Map<string, DownloadRecord>();
  private tasks = new Map<string, DownloadTask>();
  private order: string[] = [];
  private opts: Required<Omit<ManagerOptions, 'store' | 'categoryDirs' | 'getThrottleKBps'>> & ManagerOptions;
  private store: NovaStore;
  private saveTimer: NodeJS.Timeout | null = null;
  private scheduler: NodeJS.Timeout | null = null;

  constructor(opts: ManagerOptions) {
    super();
    this.opts = { maxConcurrent: 3, keepPartialsOnCancel: false, ...opts } as typeof this.opts;
    this.store = opts.store ?? new MemoryStore();
  }

  async init(): Promise<void> {
    const loaded = await this.store.load();
    for (const r of loaded) {
      // Crash recovery: anything mid-transfer becomes "paused" (resumable via .novapart + meta).
      if (r.state === 'downloading' || r.state === 'probing') r.state = 'paused';
      r.speedBps = 0;
      r.etaSeconds = null;
      this.records.set(r.id, r);
      this.order.push(r.id);
    }
    this.scheduler = setInterval(() => this.tick(), 1000);
    this.scheduler.unref?.();
    this.pump();
  }

  shutdown(): void {
    if (this.scheduler) clearInterval(this.scheduler);
    for (const task of this.tasks.values()) task.pause();
    void this.persistNow();
  }

  setMaxConcurrent(n: number): void {
    this.opts.maxConcurrent = Math.max(1, Math.min(n, 10));
    this.pump();
  }

  setDefaultDestDir(dir: string): void {
    this.opts.defaultDestDir = dir;
  }

  list(): DownloadRecord[] {
    return this.order.map((id) => this.records.get(id)).filter(Boolean) as DownloadRecord[];
  }

  get(id: string): DownloadRecord | undefined {
    return this.records.get(id);
  }

  search(query: string): DownloadRecord[] {
    const q = query.trim().toLowerCase();
    if (!q) return this.list();
    return this.list().filter(
      (r) => r.fileName.toLowerCase().includes(q) || r.url.toLowerCase().includes(q) || (r.pageTitle ?? '').toLowerCase().includes(q),
    );
  }

  private findDuplicate(url: string): DownloadRecord | undefined {
    const norm = url.trim();
    for (const r of this.records.values()) {
      if (r.url === norm && (ACTIVE_STATES.has(r.state) || r.state === 'completed')) return r;
    }
    return undefined;
  }

  async add(rawUrl: string, options: AddDownloadOptions = {}): Promise<AddResult> {
    const url = validateDownloadUrl(rawUrl, { allowPrivateNetwork: this.opts.allowPrivateNetwork });
    const dup = this.findDuplicate(url.toString());
    if (dup && !options.allowDuplicate) {
      return { record: dup, duplicate: true, existingId: dup.id };
    }

    const id = crypto.randomUUID();
    let fileName = options.fileName ? sanitizeFileName(options.fileName) : deriveFileName(url);
    let destDir = options.destDir ?? this.opts.defaultDestDir;
    const record: DownloadRecord = {
      id,
      url: url.toString(),
      fileName,
      destDir,
      totalBytes: null,
      downloadedBytes: 0,
      state: 'queued',
      category: categorize(fileName),
      supportsRange: false,
      segmented: false,
      speedBps: 0,
      avgSpeedBps: 0,
      etaSeconds: null,
      retryCount: 0,
      createdAt: Date.now(),
      updatedAt: Date.now(),
      scheduledAt: options.scheduledAt,
      source: options.source ?? 'manual',
      pageTitle: options.pageTitle,
      pageUrl: options.pageUrl,
    };

    // Probe now (fast HEAD) so the UI can show real name/size and so category
    // folders + filename de-duplication use server-provided metadata. Probe
    // failures don't block queueing — the task will surface the error on start.
    try {
      const probe = await probeUrl(url.toString(), this.opts);
      if (!options.fileName) fileName = sanitizeFileName(probe.fileName);
      record.fileName = fileName;
      record.finalUrl = probe.finalUrl;
      record.totalBytes = probe.totalBytes;
      record.supportsRange = probe.supportsRange;
      record.mime = probe.mime;
      record.category = categorize(fileName, probe.mime);
    } catch {
      /* keep URL-derived defaults */
    }

    const catDir = this.opts.categoryDirs?.[record.category];
    if (!options.destDir && catDir) destDir = catDir;
    record.destDir = destDir;
    await fs.promises.mkdir(destDir, { recursive: true }).catch(() => undefined);
    // De-duplicate against the filesystem AND against in-flight records:
    // a concurrent download may not have created its .novapart file yet.
    const takenPaths = new Set([...this.records.values()].map((r) => r.destPath).filter(Boolean));
    const finalName = deduplicatedFileName(
      record.fileName,
      (candidate) =>
        takenPaths.has(path.join(destDir, candidate)) ||
        fs.existsSync(path.join(destDir, candidate)) ||
        fs.existsSync(path.join(destDir, `${candidate}.novapart`)),
    );
    record.fileName = finalName;
    record.destPath = path.join(destDir, finalName);

    this.records.set(id, record);
    this.order.push(id);
    this.emit('update', record);
    void this.persistSoon();
    if (options.startNow !== false && !options.scheduledAt) this.pump();
    return { record, duplicate: false };
  }

  /** Adds downloads from a newline/comma separated list of URLs. Returns per-line results. */
  async addBatch(text: string, options: AddDownloadOptions = {}): Promise<{ added: AddResult[]; errors: { line: string; error: string }[] }> {
    const lines = text
      .split(/[\n,]+/)
      .map((s) => s.trim())
      .filter(Boolean);
    const added: AddResult[] = [];
    const errors: { line: string; error: string }[] = [];
    for (const line of lines) {
      try {
        added.push(await this.add(line, { ...options, source: options.source ?? 'batch' }));
      } catch (e) {
        errors.push({ line, error: e instanceof Error ? e.message : String(e) });
      }
    }
    return { added, errors };
  }

  private runningCount(): number {
    let n = 0;
    for (const r of this.records.values()) if (r.state === 'downloading' || r.state === 'probing') n++;
    return n;
  }

  private tick(): void {
    const now = Date.now();
    let changed = false;
    for (const r of this.records.values()) {
      if (r.state === 'queued' && r.scheduledAt && r.scheduledAt <= now) {
        r.scheduledAt = undefined;
        changed = true;
      }
    }
    if (changed) void this.persistSoon();
    this.pump();
  }

  private pump(): void {
    let slots = (this.opts.maxConcurrent ?? 3) - this.runningCount();
    if (slots <= 0) return;
    const now = Date.now();
    for (const id of this.order) {
      if (slots <= 0) break;
      const r = this.records.get(id);
      if (!r || r.state !== 'queued') continue;
      if (r.scheduledAt && r.scheduledAt > now) continue;
      this.startTask(r);
      slots--;
    }
  }

  private startTask(record: DownloadRecord): void {
    let task = this.tasks.get(record.id);
    if (!task) {
      task = new DownloadTask(record, this.opts);
      task.on('progress', (r) => {
        this.emit('update', r);
        void this.persistSoon();
      });
      task.on('state', (r) => {
        this.emit('update', r);
        void this.persistSoon();
        if (['completed', 'failed', 'canceled', 'paused'].includes(r.state)) this.pump();
      });
      this.tasks.set(record.id, task);
    }
    void task.start();
  }

  start(id: string): void {
    const r = this.records.get(id);
    if (!r) return;
    if (r.state === 'paused' || r.state === 'failed' || r.state === 'canceled' || r.state === 'queued') {
      r.state = 'queued';
      r.error = undefined;
      r.scheduledAt = undefined;
      this.emit('update', r);
      this.pump();
    }
  }

  pause(id: string): void {
    const r = this.records.get(id);
    if (!r) return;
    if (r.state === 'queued') {
      r.state = 'paused';
      this.emit('update', r);
      void this.persistSoon();
      return;
    }
    this.tasks.get(id)?.pause();
  }

  async cancel(id: string, deletePartial = !this.opts.keepPartialsOnCancel): Promise<void> {
    const r = this.records.get(id);
    if (!r) return;
    const task = this.tasks.get(id);
    if (task) await task.cancel(deletePartial);
    else {
      r.state = 'canceled';
      this.emit('update', r);
    }
    void this.persistSoon();
    this.pump();
  }

  retry(id: string): void {
    const r = this.records.get(id);
    if (!r) return;
    r.retryCount = 0;
    this.start(id);
  }

  /** Restart from zero: discard partial data, then queue. */
  async restart(id: string): Promise<void> {
    const r = this.records.get(id);
    if (!r || !r.destPath) return;
    await this.cancel(id, true);
    await fs.promises.rm(`${r.destPath}.novapart`, { force: true }).catch(() => undefined);
    await fs.promises.rm(`${r.destPath}.nova-meta.json`, { force: true }).catch(() => undefined);
    r.downloadedBytes = 0;
    r.segments = undefined;
    r.state = 'queued';
    r.error = undefined;
    this.emit('update', r);
    void this.persistSoon();
    this.pump();
  }

  async remove(id: string, deleteFile = false): Promise<void> {
    const r = this.records.get(id);
    if (!r) return;
    await this.cancel(id, true);
    if (deleteFile && r.destPath) await fs.promises.rm(r.destPath, { force: true }).catch(() => undefined);
    this.records.delete(id);
    this.tasks.delete(id);
    this.order = this.order.filter((x) => x !== id);
    this.emit('removed', id);
    void this.persistSoon();
  }

  move(id: string, direction: 'up' | 'down'): void {
    const idx = this.order.indexOf(id);
    if (idx < 0) return;
    const swapWith = direction === 'up' ? idx - 1 : idx + 1;
    if (swapWith < 0 || swapWith >= this.order.length) return;
    [this.order[idx], this.order[swapWith]] = [this.order[swapWith], this.order[idx]];
    this.emit('reordered', this.list());
    void this.persistSoon();
  }

  clearHistory(onlyFinished = true): void {
    for (const [id, r] of [...this.records.entries()]) {
      if (!onlyFinished || ['completed', 'failed', 'canceled'].includes(r.state)) {
        this.records.delete(id);
        this.tasks.delete(id);
      }
    }
    this.order = this.order.filter((id) => this.records.has(id));
    this.emit('reordered', this.list());
    void this.persistSoon();
  }

  /** Removes orphaned .novapart/.nova-meta files in the default folder not tracked by any record. */
  async cleanupOrphanPartials(dir?: string): Promise<number> {
    const target = dir ?? this.opts.defaultDestDir;
    let removed = 0;
    try {
      const entries = await fs.promises.readdir(target);
      const tracked = new Set<string>();
      for (const r of this.records.values()) {
        if (!r.destPath) continue;
        tracked.add(path.basename(`${r.destPath}.novapart`));
        tracked.add(path.basename(`${r.destPath}.nova-meta.json`));
        for (let i = 0; i < 16; i++) tracked.add(path.basename(`${r.destPath}.novapart.${i}`));
      }
      for (const name of entries) {
        if ((name.includes('.novapart') || name.endsWith('.nova-meta.json')) && !tracked.has(name)) {
          await fs.promises.rm(path.join(target, name), { force: true });
          removed++;
        }
      }
    } catch {
      /* folder may not exist yet */
    }
    return removed;
  }

  private persistSoon(): Promise<void> {
    if (this.saveTimer) return Promise.resolve();
    return new Promise((resolve) => {
      this.saveTimer = setTimeout(() => {
        this.saveTimer = null;
        void this.persistNow().then(resolve);
      }, 300);
      this.saveTimer.unref?.();
    });
  }

  async persistNow(): Promise<void> {
    await this.store.save(this.list()).catch(() => undefined);
  }
}
