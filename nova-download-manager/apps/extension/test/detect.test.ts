import { describe, it, expect } from 'vitest';
import { JSDOM } from 'jsdom';
import { findDirectMedia, classifyUrl } from '../src/detect';

function doc(html: string, url = 'https://site.example/watch/1'): Document {
  return new JSDOM(html, { url }).window.document as unknown as Document;
}

describe('classifyUrl', () => {
  it('classifies direct media and files', () => {
    expect(classifyUrl('https://x.test/v.mp4')).toBe('direct-video');
    expect(classifyUrl('https://x.test/a.MP3?dl=1')).toBe('direct-audio');
    expect(classifyUrl('https://x.test/f.zip')).toBe('direct-file');
    expect(classifyUrl('https://x.test/page')).toBe('page');
  });
  it('flags streaming manifests and rejects blob/data/ftp', () => {
    expect(classifyUrl('https://x.test/hls/master.m3u8')).toBe('streaming-manifest');
    expect(classifyUrl('https://x.test/dash/manifest.mpd')).toBe('streaming-manifest');
    expect(classifyUrl('blob:https://x.test/abc')).toBe('invalid');
    expect(classifyUrl('ftp://x.test/v.mp4')).toBe('invalid');
    expect(classifyUrl('not a url')).toBe('invalid');
  });
});

describe('findDirectMedia', () => {
  it('finds direct <video> and <source> files', () => {
    const d = doc(`
      <video src="https://cdn.example.com/movie.mp4" aria-label="My movie"></video>
      <video><source src="https://cdn.example.com/clip.webm" type="video/webm"></video>
      <audio><source src="/songs/track.mp3" type="audio/mpeg"></audio>
    `);
    const out = findDirectMedia(d, 'https://site.example/watch/1');
    expect(out.map((c) => c.fileName).sort()).toEqual(['clip.webm', 'movie.mp4', 'track.mp3']);
    const movie = out.find((c) => c.fileName === 'movie.mp4')!;
    expect(movie.kind).toBe('video');
    expect(movie.label).toBe('My movie');
    const song = out.find((c) => c.fileName === 'track.mp3')!;
    expect(song.url).toBe('https://site.example/songs/track.mp3'); // relative resolved
    expect(song.kind).toBe('audio');
  });

  it('ignores blob: streaming players (YouTube-style MSE)', () => {
    const d = doc(`<video src="blob:https://www.youtube.example/9f8e7d6c"></video>
                   <video><source src="https://x.test/hls/master.m3u8"></video>`);
    expect(findDirectMedia(d, 'https://www.youtube.example/watch')).toEqual([]);
  });

  it('finds direct media links but not page links, images or tracking pixels', () => {
    const d = doc(`
      <a href="https://files.example.com/episode.mp4">Watch episode</a>
      <a href="/about">About</a>
      <a href="https://files.example.com/song.mp3">Song</a>
      <img src="https://t.example.com/pixel.mp4">
      <a href="https://files.example.com/doc.pdf">PDF (not media)</a>
    `);
    const out = findDirectMedia(d, 'https://site.example/');
    expect(out.map((c) => c.fileName).sort()).toEqual(['episode.mp4', 'song.mp3']);
    expect(out.find((c) => c.fileName === 'episode.mp4')!.source).toBe('link');
  });

  it('de-duplicates and never invents candidates from extensionless URLs', () => {
    const d = doc(`
      <video src="https://cdn.example.com/v.mp4"></video>
      <a href="https://cdn.example.com/v.mp4">same file</a>
      <video src="https://cdn.example.com/stream?id=42"></video>
    `);
    const out = findDirectMedia(d, 'https://site.example/');
    expect(out).toHaveLength(1);
    expect(out[0].url).toBe('https://cdn.example.com/v.mp4');
  });

  it('handles empty pages', () => {
    expect(findDirectMedia(doc('<p>hello</p>'), 'https://a.test/')).toEqual([]);
  });
});
