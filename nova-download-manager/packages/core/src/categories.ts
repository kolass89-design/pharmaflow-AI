import * as path from 'node:path';
import type { Category } from './types';

const EXT_CATEGORY: Record<string, Category> = {};
function reg(category: Category, exts: string[]) {
  for (const e of exts) EXT_CATEGORY[e] = category;
}
reg('video', ['.mp4', '.mkv', '.webm', '.mov', '.avi', '.m4v', '.ts', '.wmv', '.flv', '.3gp']);
reg('audio', ['.mp3', '.m4a', '.aac', '.ogg', '.opus', '.wav', '.flac', '.wma', '.aif', '.aiff']);
reg('documents', ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.md', '.rtf', '.odt', '.ods', '.csv', '.epub']);
reg('archives', ['.zip', '.7z', '.rar', '.tar', '.gz', '.bz2', '.xz', '.tgz', '.iso', '.dmg']);
reg('images', ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.ico', '.avif', '.tif', '.tiff']);
reg('applications', ['.exe', '.msi', '.apk', '.aab', '.deb', '.rpm', '.appimage', '.msix', '.bat', '.cmd', '.ps1', '.jar']);

export function categorize(fileName: string, mime?: string): Category {
  const ext = path.extname(fileName).toLowerCase();
  if (ext && EXT_CATEGORY[ext]) return EXT_CATEGORY[ext];
  if (mime) {
    const m = mime.split(';')[0].trim().toLowerCase();
    if (m.startsWith('video/')) return 'video';
    if (m.startsWith('audio/')) return 'audio';
    if (m.startsWith('image/')) return 'images';
    if (m === 'application/pdf' || m.startsWith('text/')) return 'documents';
    if (m.includes('zip') || m.includes('compressed') || m.includes('tar')) return 'archives';
    if (m.includes('android.package') || m.includes('msdownload') || m.includes('octet-stream')) return 'applications';
  }
  return 'other';
}

/** Executable-ish files must never be auto-opened/run by Nova; the UI warns instead. */
const EXECUTABLE_EXTS = new Set(['.exe', '.msi', '.bat', '.cmd', '.ps1', '.scr', '.com', '.jar', '.apk', '.msix', '.appimage', '.deb', '.rpm']);
export function isExecutableFile(fileName: string): boolean {
  return EXECUTABLE_EXTS.has(path.extname(fileName).toLowerCase());
}
