import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { DownloadRecord } from '../types';
import { nova } from '../types';
import { baseName, formatTime } from '../lib/format';

interface Props {
  completedMedia: DownloadRecord[];
  playRequest: { path: string; nonce: number } | null;
  onToast: (k: 'info' | 'warn' | 'bad', t: string, b?: string) => void;
}

const AUDIO_EXT = /\.(mp3|m4a|aac|ogg|opus|wav|flac)$/i;

export function PlayerView({ completedMedia, playRequest, onToast }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const [extraFiles, setExtraFiles] = useState<string[]>([]);
  const [current, setCurrent] = useState<string | null>(null);
  const [src, setSrc] = useState<string>('');
  const [playing, setPlaying] = useState(false);
  const [time, setTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.9);
  const [speed, setSpeed] = useState(1);
  const [error, setError] = useState('');
  const [positions, setPositions] = useState<Record<string, number>>({});
  const positionsRef = useRef<Record<string, number>>({});
  positionsRef.current = positions;

  const playlist = useMemo(() => {
    const fromDownloads = completedMedia.map((r) => r.destPath!).filter(Boolean);
    return [...new Set([...fromDownloads, ...extraFiles])];
  }, [completedMedia, extraFiles]);

  // Load persisted playlist additions + resume positions once.
  useEffect(() => {
    void nova.getPlayerState().then((s) => {
      setPositions(s.positions ?? {});
      setExtraFiles(s.playlist ?? []);
    }).catch(() => undefined);
  }, []);

  const persist = useCallback((files: string[], pos: Record<string, number>) => {
    void nova.savePlayerState({ playlist: files, positions: pos }).catch(() => undefined);
  }, []);

  const playPath = useCallback(async (p: string) => {
    setError('');
    try {
      const url = await nova.registerMedia(p);
      setCurrent(p);
      setSrc(url);
    } catch (e) {
      onToast('bad', 'Cannot play file', e instanceof Error ? e.message : String(e));
    }
  }, [onToast]);

  // External play requests (from a download card).
  useEffect(() => {
    if (playRequest) void playPath(playRequest.path);
  }, [playRequest, playPath]);

  // When src changes the element reloads; restore position + autoplay.
  useEffect(() => {
    const v = videoRef.current;
    if (!v || !src || !current) return;
    const onMeta = () => {
      const pos = positionsRef.current[current];
      if (pos && pos > 3 && pos < (v.duration || Infinity) - 5) v.currentTime = pos;
      v.volume = volume;
      v.playbackRate = speed;
      void v.play().catch(() => undefined);
    };
    v.addEventListener('loadedmetadata', onMeta);
    return () => v.removeEventListener('loadedmetadata', onMeta);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [src, current]);

  // Save position every 5s while playing + on pause.
  useEffect(() => {
    const iv = setInterval(() => {
      const v = videoRef.current;
      if (v && current && !v.paused) {
        const next = { ...positionsRef.current, [current]: v.currentTime };
        setPositions(next);
        persist(extraFiles, next);
      }
    }, 5000);
    return () => clearInterval(iv);
  }, [current, extraFiles, persist]);

  const idx = current ? playlist.indexOf(current) : -1;
  const next = useCallback(() => { if (idx >= 0 && idx < playlist.length - 1) void playPath(playlist[idx + 1]); }, [idx, playlist, playPath]);
  const prev = useCallback(() => { if (idx > 0) void playPath(playlist[idx - 1]); }, [idx, playlist, playPath]);

  async function addFiles() {
    const files = await nova.pickMediaFiles();
    if (!files.length) return;
    const merged = [...new Set([...extraFiles, ...files])];
    setExtraFiles(merged);
    persist(merged, positions);
    if (!current) void playPath(files[0]);
  }

  function toggle() {
    const v = videoRef.current;
    if (!v) return;
    if (v.paused) void v.play().catch(() => undefined);
    else v.pause();
  }

  function seek(t: number) {
    const v = videoRef.current;
    if (v) v.currentTime = t;
  }

  function fullscreen() {
    const el = stageRef.current;
    if (!el) return;
    if (document.fullscreenElement) void document.exitFullscreen();
    else void el.requestFullscreen().catch(() => undefined);
  }

  // Keyboard shortcuts (Windows): Space, arrows, F fullscreen, M mute, N/P next/prev.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      const v = videoRef.current;
      if (!v || !current) return;
      if (e.code === 'Space') { e.preventDefault(); toggle(); }
      else if (e.key === 'ArrowRight') seek(Math.min(duration || 0, v.currentTime + 10));
      else if (e.key === 'ArrowLeft') seek(Math.max(0, v.currentTime - 10));
      else if (e.key === 'ArrowUp') { e.preventDefault(); const nv = Math.min(1, volume + 0.05); setVolume(nv); v.volume = nv; }
      else if (e.key === 'ArrowDown') { e.preventDefault(); const nv = Math.max(0, volume - 0.05); setVolume(nv); v.volume = nv; }
      else if (e.key.toLowerCase() === 'f') fullscreen();
      else if (e.key.toLowerCase() === 'm') { v.muted = !v.muted; }
      else if (e.key.toLowerCase() === 'n') next();
      else if (e.key.toLowerCase() === 'p') prev();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  const isAudio = current ? AUDIO_EXT.test(current) : false;

  return (
    <div className="player-wrap">
      <div>
        <div className="player-stage" ref={stageRef}>
          {isAudio && <div className="audio-art">🎵</div>}
          <video
            ref={videoRef}
            src={src || undefined}
            style={isAudio ? { height: 0 } : undefined}
            onPlay={() => setPlaying(true)}
            onPause={() => {
              setPlaying(false);
              const v = videoRef.current;
              if (v && current) {
                const nxt = { ...positionsRef.current, [current]: v.currentTime };
                setPositions(nxt);
                persist(extraFiles, nxt);
              }
            }}
            onTimeUpdate={() => setTime(videoRef.current?.currentTime ?? 0)}
            onLoadedMetadata={() => setDuration(videoRef.current?.duration ?? 0)}
            onEnded={() => next()}
            onError={() => {
              if (!src) return;
              setError('This file could not be played. Nova’s player uses the Chromium media engine, which supports MP4 (H.264/AAC), WebM, MP3, M4A/AAC, OGG/Opus and WAV. Other codecs (e.g. HEVC/H.265, MKV containers, AVI) are not supported on every system — try opening the file in a dedicated player like VLC.');
            }}
          />
          <div className="player-controls">
            <div style={{ fontWeight: 650, marginBottom: 4 }}>{current ? baseName(current) : 'Nothing playing'}</div>
            <input className="seek" type="range" min={0} max={duration || 0} step={0.1} value={time} onChange={(e) => seek(parseFloat(e.target.value))} disabled={!current} />
            <div className="ctl-row">
              <button className="ctl-btn" onClick={prev} disabled={idx <= 0} title="Previous (P)">⏮</button>
              <button className="ctl-btn main" onClick={toggle} disabled={!current} title="Play/Pause (Space)">{playing ? '⏸' : '▶'}</button>
              <button className="ctl-btn" onClick={next} disabled={idx < 0 || idx >= playlist.length - 1} title="Next (N)">⏭</button>
              <span className="small muted">{formatTime(time)} / {formatTime(duration)}</span>
              <span style={{ flex: 1 }} />
              <span className="small muted">🔊</span>
              <input className="vol" type="range" min={0} max={1} step={0.02} value={volume} onChange={(e) => { const nv = parseFloat(e.target.value); setVolume(nv); if (videoRef.current) videoRef.current.volume = nv; }} />
              <select className="speed" value={speed} onChange={(e) => { const s = parseFloat(e.target.value); setSpeed(s); if (videoRef.current) videoRef.current.playbackRate = s; }}>
                {[0.5, 0.75, 1, 1.25, 1.5, 2].map((s) => <option key={s} value={s}>{s}×</option>)}
              </select>
              {!isAudio && <button className="ctl-btn" onClick={fullscreen} disabled={!current} title="Fullscreen (F)">⛶</button>}
            </div>
            {error && <div className="player-error">{error}</div>}
            <p className="small muted" style={{ marginTop: 8 }}>
              Shortcuts: <span className="kbd">Space</span> play/pause · <span className="kbd">←</span>/<span className="kbd">→</span> seek 10s ·{' '}
              <span className="kbd">↑</span>/<span className="kbd">↓</span> volume · <span className="kbd">F</span> fullscreen · <span className="kbd">M</span> mute ·{' '}
              <span className="kbd">N</span>/<span className="kbd">P</span> next/previous. Playback position is remembered per file.
            </p>
          </div>
        </div>
      </div>
      <div className="panel" style={{ marginBottom: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <h2 style={{ margin: 0 }}>Playlist</h2>
          <button className="btn small" onClick={() => void addFiles()}>＋ Add files…</button>
        </div>
        <p className="small muted">Completed video/audio downloads appear here automatically. You can also add any media already on this computer — no download needed.</p>
        <div className="playlist">
          {playlist.length === 0 && <p className="muted small">Playlist is empty.</p>}
          {playlist.map((p) => (
            <button key={p} className={`playlist-item ${p === current ? 'on' : ''}`} onClick={() => void playPath(p)}>
              <span>{AUDIO_EXT.test(p) ? '🎵' : '🎬'}</span>
              <span className="nm">{baseName(p)}</span>
              {positions[p] ? <span className="small muted">{formatTime(positions[p])}</span> : null}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
