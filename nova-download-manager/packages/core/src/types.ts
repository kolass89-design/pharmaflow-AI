export type DownloadState =
  | 'queued'
  | 'probing'
  | 'downloading'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'canceled';

export type Category =
  | 'video'
  | 'audio'
  | 'documents'
  | 'archives'
  | 'images'
  | 'applications'
  | 'other';

export type DownloadSource = 'manual' | 'extension' | 'clipboard' | 'batch' | 'share' | 'detected';

export interface SegmentInfo {
  index: number;
  /** inclusive byte offset in the final file */
  start: number;
  /** inclusive byte offset in the final file */
  end: number;
  /** bytes downloaded within this segment */
  downloaded: number;
}

export interface DownloadRecord {
  id: string;
  url: string;
  finalUrl?: string;
  fileName: string;
  destDir: string;
  destPath?: string;
  totalBytes: number | null;
  downloadedBytes: number;
  state: DownloadState;
  category: Category;
  mime?: string;
  supportsRange: boolean;
  segmented: boolean;
  segments?: SegmentInfo[];
  speedBps: number;
  avgSpeedBps: number;
  etaSeconds: number | null;
  error?: string;
  retryCount: number;
  createdAt: number;
  updatedAt: number;
  completedAt?: number;
  scheduledAt?: number;
  source: DownloadSource;
  pageTitle?: string;
  pageUrl?: string;
  sha256?: string;
}

export interface AddDownloadOptions {
  destDir?: string;
  fileName?: string;
  startNow?: boolean;
  scheduledAt?: number;
  source?: DownloadSource;
  pageTitle?: string;
  pageUrl?: string;
  /** allow adding even if an identical active/completed download exists */
  allowDuplicate?: boolean;
}

export interface EngineOptions {
  /** Block localhost / private / link-local destinations (SSRF & bridge-abuse guard). Default false = blocked. */
  allowPrivateNetwork?: boolean;
  maxRedirects?: number;
  userAgent?: string;
  /** files at or above this size may use segmented downloading (if server supports Range) */
  segmentThresholdBytes?: number;
  maxSegments?: number;
  enableSegmented?: boolean;
  /** automatic retries for transient failures */
  maxAutoRetries?: number;
  /** returns current global bandwidth cap in KB/s, or null for unlimited */
  getThrottleKBps?: () => number | null;
  connectTimeoutMs?: number;
}

export interface ProbeResult {
  finalUrl: string;
  totalBytes: number | null;
  supportsRange: boolean;
  fileName: string;
  mime?: string;
  etag?: string;
  lastModified?: string;
}
