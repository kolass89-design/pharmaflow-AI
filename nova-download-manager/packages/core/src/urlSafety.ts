import * as net from 'node:net';
import * as path from 'node:path';

export class UnsafeUrlError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'UnsafeUrlError';
  }
}

function isPrivateIPv4(ip: string): boolean {
  const parts = ip.split('.').map((p) => parseInt(p, 10));
  if (parts.length !== 4 || parts.some((n) => Number.isNaN(n))) return false;
  const [a, b] = parts;
  if (a === 10) return true;
  if (a === 127) return true;
  if (a === 172 && b >= 16 && b <= 31) return true;
  if (a === 192 && b === 168) return true;
  if (a === 169 && b === 254) return true; // link-local
  if (a === 0) return true;
  if (a === 100 && b >= 64 && b <= 127) return true; // CGNAT
  return false;
}

function isPrivateIPv6(ip: string): boolean {
  const lower = ip.toLowerCase();
  if (lower === '::1' || lower === '::') return true;
  if (lower.startsWith('fe80:')) return true; // link-local
  if (lower.startsWith('fc') || lower.startsWith('fd')) return true; // unique local
  // IPv4-mapped
  const mapped = lower.match(/::ffff:(\d+\.\d+\.\d+\.\d+)$/);
  if (mapped) return isPrivateIPv4(mapped[1]);
  return false;
}

/**
 * Validates a download URL.
 * - Only http: and https: are allowed.
 * - When allowPrivateNetwork is false (default), literal private/loopback IPs,
 *   "localhost" and *.local hostnames are rejected. This prevents the browser
 *   extension bridge / clipboard ingestion from being abused to probe the LAN.
 *   Note: hostname→DNS resolution checks are intentionally out of scope for a
 *   desktop downloader (the user supplies URLs directly); see SECURITY.md.
 */
export function validateDownloadUrl(raw: string, opts: { allowPrivateNetwork?: boolean } = {}): URL {
  let url: URL;
  try {
    url = new URL(String(raw).trim());
  } catch {
    throw new UnsafeUrlError('Invalid URL');
  }
  if (url.protocol !== 'http:' && url.protocol !== 'https:') {
    throw new UnsafeUrlError(`Unsupported protocol "${url.protocol}". Only HTTP and HTTPS downloads are supported.`);
  }
  if (!opts.allowPrivateNetwork) {
    const host = url.hostname.toLowerCase().replace(/^\[|\]$/g, '');
    if (host === 'localhost' || host.endsWith('.local') || host.endsWith('.localhost')) {
      throw new UnsafeUrlError('Downloads from localhost are blocked. Enable "Allow private network downloads" in Settings if you trust this source.');
    }
    if (net.isIP(host)) {
      const priv = host.includes(':') ? isPrivateIPv6(host) : isPrivateIPv4(host);
      if (priv) {
        throw new UnsafeUrlError('Downloads from private/local network addresses are blocked. Enable "Allow private network downloads" in Settings if you trust this source.');
      }
    }
  }
  return url;
}

/** Redact credentials so URLs can be safely shown in logs / error messages. */
export function redactUrl(raw: string): string {
  try {
    const u = new URL(raw);
    if (u.username) u.username = '***';
    if (u.password) u.password = '***';
    return u.toString();
  } catch {
    return '(invalid url)';
  }
}

const WINDOWS_RESERVED = /^(con|prn|aux|nul|com[1-9]|lpt[1-9])(\..*)?$/i;

/**
 * Sanitizes a server- or user-supplied file name:
 * strips directories (path traversal), control chars and illegal characters,
 * neutralises Windows reserved device names, trims trailing dots/spaces,
 * and caps length while preserving a sane extension.
 */
export function sanitizeFileName(name: string | undefined | null, fallback = 'download'): string {
  let base = (name ?? '').toString();
  // Take only the final path segment, for both POSIX and Windows separators.
  base = base.replace(/\\/g, '/').split('/').pop() ?? '';
  // Remove control characters and characters illegal on Windows/macOS/Linux.
  // eslint-disable-next-line no-control-regex
  base = base.replace(/[<>:"|?*\u0000-\u001f\u007f]/g, '_');
  base = base.replace(/\s+/g, ' ').trim();
  base = base.replace(/[. ]+$/g, ''); // trailing dots/spaces are invalid on Windows
  base = base.replace(/^\.+/, '_'); // no hidden/dot-leading names
  if (!base) base = fallback;
  if (WINDOWS_RESERVED.test(base)) base = `_${base}`;
  if (base.length > 200) {
    const dot = base.lastIndexOf('.');
    const ext = dot > 0 && base.length - dot <= 12 ? base.slice(dot) : '';
    base = base.slice(0, 200 - ext.length) + ext;
  }
  return base;
}

/** Parses a filename out of a Content-Disposition header (RFC 5987 aware). */
export function fileNameFromContentDisposition(header: string | undefined): string | undefined {
  if (!header) return undefined;
  const star = header.match(/filename\*\s*=\s*([^']*)'[^']*'([^;]+)/i);
  if (star) {
    try {
      return sanitizeFileName(decodeURIComponent(star[2].trim()));
    } catch {
      /* fall through */
    }
  }
  const plain = header.match(/filename\s*=\s*("[^"]*"|[^;]+)/i);
  if (plain) {
    let v = plain[1].trim();
    if (v.startsWith('"') && v.endsWith('"')) v = v.slice(1, -1);
    try {
      v = decodeURIComponent(v);
    } catch {
      /* keep raw */
    }
    return sanitizeFileName(v);
  }
  return undefined;
}

const MIME_EXT: Record<string, string> = {
  'application/pdf': '.pdf',
  'application/zip': '.zip',
  'application/x-7z-compressed': '.7z',
  'application/x-rar-compressed': '.rar',
  'application/json': '.json',
  'text/plain': '.txt',
  'image/jpeg': '.jpg',
  'image/png': '.png',
  'image/gif': '.gif',
  'image/webp': '.webp',
  'video/mp4': '.mp4',
  'video/webm': '.webm',
  'video/quicktime': '.mov',
  'audio/mpeg': '.mp3',
  'audio/mp4': '.m4a',
  'audio/ogg': '.ogg',
  'audio/wav': '.wav',
  'application/vnd.android.package-archive': '.apk',
  'application/x-msdownload': '.exe',
  'application/x-msi': '.msi',
};

/** Best-effort file name from URL path + headers. */
export function deriveFileName(url: URL, contentDisposition?: string, mime?: string): string {
  const fromHeader = fileNameFromContentDisposition(contentDisposition);
  if (fromHeader && fromHeader !== 'download') return fromHeader;
  let segment = '';
  try {
    segment = decodeURIComponent(url.pathname.split('/').filter(Boolean).pop() ?? '');
  } catch {
    segment = url.pathname.split('/').filter(Boolean).pop() ?? '';
  }
  let name = sanitizeFileName(segment);
  if (name === 'download' || !path.extname(name)) {
    const ext = mime ? MIME_EXT[mime.split(';')[0].trim().toLowerCase()] : undefined;
    if (ext && !name.toLowerCase().endsWith(ext)) name += ext;
  }
  return name;
}

/** If a file already exists at destPath, returns "name (1).ext" style alternative path. Caller checks existence. */
export function deduplicatedFileName(fileName: string, exists: (candidate: string) => boolean): string {
  if (!exists(fileName)) return fileName;
  const ext = path.extname(fileName);
  const stem = ext ? fileName.slice(0, -ext.length) : fileName;
  for (let i = 1; i < 10000; i++) {
    const candidate = `${stem} (${i})${ext}`;
    if (!exists(candidate)) return candidate;
  }
  return `${stem} (${Date.now()})${ext}`;
}
