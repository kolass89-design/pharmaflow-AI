import * as fs from 'node:fs';
import * as path from 'node:path';
import type { DownloadRecord } from './types';

export interface NovaStore {
  load(): Promise<DownloadRecord[]>;
  save(records: DownloadRecord[]): Promise<void>;
}

export class MemoryStore implements NovaStore {
  private data: DownloadRecord[] = [];
  async load(): Promise<DownloadRecord[]> {
    return JSON.parse(JSON.stringify(this.data));
  }
  async save(records: DownloadRecord[]): Promise<void> {
    this.data = JSON.parse(JSON.stringify(records));
  }
}

/** Atomic JSON-file persistence (write temp + rename) so a crash cannot corrupt history. */
export class JsonFileStore implements NovaStore {
  constructor(private filePath: string) {}

  async load(): Promise<DownloadRecord[]> {
    try {
      const raw = await fs.promises.readFile(this.filePath, 'utf8');
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  async save(records: DownloadRecord[]): Promise<void> {
    const dir = path.dirname(this.filePath);
    await fs.promises.mkdir(dir, { recursive: true });
    const tmp = `${this.filePath}.tmp`;
    await fs.promises.writeFile(tmp, JSON.stringify(records, null, 1), 'utf8');
    await fs.promises.rename(tmp, this.filePath);
  }
}
