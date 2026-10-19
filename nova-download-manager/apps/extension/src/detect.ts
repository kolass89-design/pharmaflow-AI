/**
 * Pure, testable media-detection logic.
 *
 * Nova only treats DIRECT media files as downloadable: plain http(s) URLs
 * whose path ends in a known media extension, referenced by <video>,
 * <audio>, <source> or <a> elements. It deliberately excludes:
 *  - blob: URLs (MediaSource/adaptive players used by streaming sites)
 *  - HLS (.m3u8) / DASH (.mpd) manifests
 *  - data: URLs and non-http(s) schemes
 * This keeps detection honest: no stream scraping, no session/cookie use,
 * no circumvention. Sizes are unknown at this layer (CORS usually prevents
 * probing); the desktop app probes the real size/type before downloading.
 */

export interface MediaCandidate {
  url: string;
  kind: 'video' | 'audio';
  fileName: string;
  mimeGuess: string;
  source: 'video-tag' | 'audio-tag' | 'link';
  /** whatever title-ish context we could find (aria-label, title attr, link text) */
  label?: string;
}

const VIDEO_EXT: Record<string, string> = {
  mp4: 'video/mp4', webm: 'video/webm', mov: 'video/quicktime', m4v: 'video/mp4', mkv: 'video/x-matroska',
};
const AUDIO_EXT: Record<string, string> = {
  mp3: 'audio/mpeg', m4a: 'audio/mp4', aac: 'audio/aac', ogg: 'audio/ogg', opus: 'audio/opus', wav: 'audio/wav', flac: 'audio/flac',
};
const FILE_EXTS = new Set([
  'zip', '7z', 'rar', 'tar', 'gz', 'bz2', 'xz', 'iso', 'dmg', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
  'exe', 'msi', 'apk', 'deb', 'rpm', 'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'csv', 'json', 'txt',
]);

export type UrlClass =
  | 'direct-video'
  | 'direct-audio'
  | 'direct-file'
  | 'streaming-manifest'
  | 'page'
  | 'invalid';

export function extOf(urlString: string): string {
  try {
    const path = new URL(urlString).pathname;
    const dot = path.lastIndexOf('.');
    const slash = path.lastIndexOf('/');
    if (dot <= slash) return '';
    return path.slice(dot + 1).toLowerCase();
  } catch {
    return '';
  }
}

export function classifyUrl(urlString: string): UrlClass {
  let u: URL;
  try {
    u = new URL(urlString);
  } catch {
    return 'invalid';
  }
  if (u.protocol !== 'http:' && u.protocol !== 'https:') return 'invalid';
  const ext = extOf(urlString);
  if (ext === 'm3u8' || ext === 'mpd') return 'streaming-manifest';
  if (ext in VIDEO_EXT) return 'direct-video';
  if (ext in AUDIO_EXT) return 'direct-audio';
  if (FILE_EXTS.has(ext)) return 'direct-file';
  return 'page';
}

export function fileNameOf(urlString: string): string {
  try {
    const seg = new URL(urlString).pathname.split('/').filter(Boolean).pop() ?? 'media';
    return decodeURIComponent(seg);
  } catch {
    return 'media';
  }
}

function resolve(raw: string | null | undefined, base: string): string | null {
  if (!raw) return null;
  const trimmed = raw.trim();
  if (!trimmed || trimmed.startsWith('blob:') || trimmed.startsWith('data:') || trimmed.startsWith('javascript:')) return null;
  try {
    return new URL(trimmed, base).toString();
  } catch {
    return null;
  }
}

/** Scans a document for direct media files. `doc` is structurally typed for testability. */
export function findDirectMedia(doc: Document, baseUrl: string): MediaCandidate[] {
  const found = new Map<string, MediaCandidate>();

  const consider = (raw: string | null | undefined, source: MediaCandidate['source'], label?: string, typeHint?: string | null) => {
    const url = resolve(raw, baseUrl);
    if (!url) return;
    const cls = classifyUrl(url);
    let kind: 'video' | 'audio' | null = null;
    let mime = '';
    let ext = extOf(url);
    if (cls === 'direct-video') { kind = 'video'; mime = VIDEO_EXT[ext]; }
    else if (cls === 'direct-audio') { kind = 'audio'; mime = AUDIO_EXT[ext]; }
    else if (typeHint && (typeHint.startsWith('video/mp4') || typeHint.startsWith('video/webm'))) { kind = 'video'; mime = typeHint; ext = 'mp4'; }
    else if (typeHint && (typeHint.startsWith('audio/mpeg') || typeHint.startsWith('audio/mp4') || typeHint.startsWith('audio/ogg'))) { kind = 'audio'; mime = typeHint; ext = 'mp3'; }
    if (!kind) return; // not a direct media file — never guess
    if (found.has(url)) return;
    let fileName = fileNameOf(url);
    if (!fileName.includes('.')) fileName = `${fileName || 'media'}.${ext || (kind === 'video' ? 'mp4' : 'mp3')}`;
    found.set(url, { url, kind, fileName, mimeGuess: mime, source, label: label?.trim()?.slice(0, 120) || undefined });
  };

  doc.querySelectorAll('video').forEach((v) => {
    const el = v as HTMLVideoElement;
    const label = el.getAttribute('aria-label') || el.title || doc.title;
    consider(el.getAttribute('src') || el.currentSrc, 'video-tag', label);
    el.querySelectorAll('source').forEach((s) => consider(s.getAttribute('src'), 'video-tag', label, s.getAttribute('type')));
  });
  doc.querySelectorAll('audio').forEach((a) => {
    const el = a as HTMLAudioElement;
    const label = el.getAttribute('aria-label') || el.title || doc.title;
    consider(el.getAttribute('src') || el.currentSrc, 'audio-tag', label);
    el.querySelectorAll('source').forEach((s) => consider(s.getAttribute('src'), 'audio-tag', label, s.getAttribute('type')));
  });
  doc.querySelectorAll('a[href]').forEach((a) => {
    consider(a.getAttribute('href'), 'link', a.textContent || undefined);
  });

  return [...found.values()];
}
