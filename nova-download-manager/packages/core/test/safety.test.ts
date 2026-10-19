import { describe, it, expect } from 'vitest';
import {
  sanitizeFileName,
  validateDownloadUrl,
  fileNameFromContentDisposition,
  deriveFileName,
} from '../src/urlSafety';
import { categorize, isExecutableFile } from '../src/categories';

describe('sanitizeFileName', () => {
  it('strips path traversal', () => {
    expect(sanitizeFileName('../../etc/passwd')).toBe('passwd');
    expect(sanitizeFileName('C:\\Windows\\evil.exe')).toBe('evil.exe');
    expect(sanitizeFileName('/abs/path/movie.mp4')).toBe('movie.mp4');
  });
  it('replaces illegal characters', () => {
    expect(sanitizeFileName('a<b>:"|?*.mp4')).toBe('a_b______.mp4');
  });
  it('neutralises Windows reserved names', () => {
    expect(sanitizeFileName('CON.mp4')).toBe('_CON.mp4');
    expect(sanitizeFileName('nul')).toBe('_nul');
  });
  it('handles empty / dot-only names', () => {
    expect(sanitizeFileName('')).toBe('download');
    expect(sanitizeFileName('...')).toBe('download');
    expect(sanitizeFileName(undefined)).toBe('download');
  });
  it('caps very long names keeping extension', () => {
    const out = sanitizeFileName('a'.repeat(300) + '.mp4');
    expect(out.length).toBeLessThanOrEqual(200);
    expect(out.endsWith('.mp4')).toBe(true);
  });
});

describe('validateDownloadUrl', () => {
  it('accepts public http/https', () => {
    expect(validateDownloadUrl('https://example.com/f.mp4').hostname).toBe('example.com');
    expect(validateDownloadUrl('http://downloads.example.org/a.zip')).toBeTruthy();
  });
  it('rejects other protocols', () => {
    expect(() => validateDownloadUrl('ftp://example.com/f')).toThrow(/protocol/i);
    expect(() => validateDownloadUrl('file:///etc/passwd')).toThrow(/protocol/i);
    expect(() => validateDownloadUrl('javascript:alert(1)')).toThrow();
  });
  it('rejects garbage', () => {
    expect(() => validateDownloadUrl('not a url')).toThrow(/invalid url/i);
  });
  it('blocks private/loopback by default, allows when opted in', () => {
    expect(() => validateDownloadUrl('http://127.0.0.1:8000/f.bin')).toThrow(/private|blocked/i);
    expect(() => validateDownloadUrl('http://192.168.1.20/f.bin')).toThrow(/private|blocked/i);
    expect(() => validateDownloadUrl('http://localhost/f.bin')).toThrow(/localhost|blocked/i);
    expect(() => validateDownloadUrl('http://[::1]/f.bin')).toThrow(/private|blocked/i);
    expect(validateDownloadUrl('http://127.0.0.1:8000/f.bin', { allowPrivateNetwork: true })).toBeTruthy();
  });
});

describe('fileNameFromContentDisposition', () => {
  it('parses plain and RFC5987 forms', () => {
    expect(fileNameFromContentDisposition('attachment; filename="movie.mp4"')).toBe('movie.mp4');
    expect(fileNameFromContentDisposition("attachment; filename*=UTF-8''my%20file%20(1).zip")).toBe('my file (1).zip');
  });
  it('sanitizes hostile names', () => {
    expect(fileNameFromContentDisposition('attachment; filename="../../evil?.txt"')).toBe('evil_.txt');
  });
});

describe('deriveFileName', () => {
  it('uses URL path and mime-derived extension', () => {
    expect(deriveFileName(new URL('https://x.test/media/clip'))).toBe('clip');
    expect(deriveFileName(new URL('https://x.test/media/clip'), undefined, 'video/mp4')).toBe('clip.mp4');
    expect(deriveFileName(new URL('https://x.test/a%20b.mp4?dl=1'))).toBe('a b.mp4');
  });
});

describe('categorize / isExecutableFile', () => {
  it('categorizes by extension and mime', () => {
    expect(categorize('a.mp4')).toBe('video');
    expect(categorize('a.mp3')).toBe('audio');
    expect(categorize('a.pdf')).toBe('documents');
    expect(categorize('a.zip')).toBe('archives');
    expect(categorize('a.png')).toBe('images');
    expect(categorize('setup.exe')).toBe('applications');
    expect(categorize('noext', 'video/webm')).toBe('video');
    expect(categorize('noext')).toBe('other');
  });
  it('flags executables', () => {
    expect(isExecutableFile('setup.exe')).toBe(true);
    expect(isExecutableFile('app.apk')).toBe(true);
    expect(isExecutableFile('movie.mp4')).toBe(false);
  });
});
