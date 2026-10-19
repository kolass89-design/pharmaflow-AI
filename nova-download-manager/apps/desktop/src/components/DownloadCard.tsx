import React from 'react';
import type { DownloadRecord } from '../types';
import { nova } from '../types';
import { CATEGORY_ICON, STATE_LABEL, formatBytes, formatSpeed, formatEta, timeAgo } from '../lib/format';

interface Props {
  record: DownloadRecord;
  onToast: (kind: 'info' | 'warn' | 'bad', title: string, body?: string) => void;
  onPlay: (record: DownloadRecord) => void;
}

export function DownloadCard({ record: r, onToast, onPlay }: Props) {
  const pct = r.totalBytes ? Math.min(100, (r.downloadedBytes / r.totalBytes) * 100) : null;
  const active = r.state === 'downloading' || r.state === 'probing';
  const playable = r.state === 'completed' && (r.category === 'video' || r.category === 'audio');

  async function open() {
    const res = await nova.openFile(r.id);
    if (!res.ok) onToast('warn', 'Heads up', res.message);
  }

  async function remove(deleteFile: boolean) {
    if (deleteFile && !window.confirm(`Delete "${r.fileName}" from disk permanently?`)) return;
    await nova.remove(r.id, deleteFile);
  }

  return (
    <div className="dl-card">
      <div className="dl-icon">{CATEGORY_ICON[r.category] ?? '📦'}</div>
      <div className="dl-main">
        <div className="dl-name">
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.fileName}</span>
          <span className={`chip ${r.state}`}>{STATE_LABEL[r.state] ?? r.state}</span>
          {r.segmented && <span className="chip">Segmented</span>}
          {!r.supportsRange && (r.state === 'paused' || r.state === 'failed') && r.totalBytes !== null && (
            <span className="chip">Resume not supported by server</span>
          )}
        </div>
        <div className="dl-meta">
          <span>{formatBytes(r.downloadedBytes)}{r.totalBytes !== null ? ` of ${formatBytes(r.totalBytes)}` : ''}{pct !== null ? ` · ${pct.toFixed(1)}%` : ''}</span>
          {active && <span>⚡ {formatSpeed(r.speedBps)}</span>}
          {active && r.etaSeconds !== null && <span>⏳ {formatEta(r.etaSeconds)} left</span>}
          {r.state === 'completed' && r.avgSpeedBps > 0 && <span>avg {formatSpeed(r.avgSpeedBps)}</span>}
          {r.scheduledAt && r.state === 'queued' && <span>🕒 starts {new Date(r.scheduledAt).toLocaleString()}</span>}
          <span className="muted">{timeAgo(r.createdAt)}</span>
          {r.retryCount > 0 && <span>retries: {r.retryCount}</span>}
        </div>
        <div className="dl-url" title={r.url}>{r.pageTitle ? `${r.pageTitle} · ` : ''}{r.url}</div>
        {r.state !== 'completed' && (
          <div className={`progress ${r.state === 'failed' ? 'bad' : ''}`}>
            <div style={{ width: `${pct ?? (active ? 4 : 0)}%` }} />
          </div>
        )}
        {r.state === 'completed' && <div className="progress done"><div style={{ width: '100%' }} /></div>}
        {r.error && r.state === 'failed' && <div className="dl-error">{r.error}{!r.supportsRange ? ' This server does not support resuming, so a retry restarts from the beginning.' : ''}</div>}
      </div>
      <div className="dl-actions">
        {playable && <button className="icon-btn" title="Play in Nova player" onClick={() => onPlay(r)}>▶️</button>}
        {active && <button className="icon-btn" title="Pause" onClick={() => void nova.pause(r.id)}>⏸️</button>}
        {(r.state === 'paused' || r.state === 'queued') && <button className="icon-btn" title={r.state === 'paused' ? 'Resume' : 'Start'} onClick={() => void nova.start(r.id)}>▶️</button>}
        {r.state === 'failed' && <button className="icon-btn" title="Retry" onClick={() => void nova.retry(r.id)}>🔄</button>}
        {r.state === 'queued' && (
          <>
            <button className="icon-btn" title="Move up in queue" onClick={() => void nova.move(r.id, 'up')}>↑</button>
            <button className="icon-btn" title="Move down in queue" onClick={() => void nova.move(r.id, 'down')}>↓</button>
          </>
        )}
        {r.state === 'completed' && <button className="icon-btn" title="Open file" onClick={() => void open()}>📂</button>}
        <button className="icon-btn" title="Show in folder" onClick={() => void nova.showInFolder(r.id)}>🗂️</button>
        {(active || r.state === 'queued' || r.state === 'paused') && (
          <button className="icon-btn" title="Cancel download" onClick={() => void nova.cancel(r.id)}>⏹️</button>
        )}
        {(r.state === 'completed' || r.state === 'failed' || r.state === 'canceled') && (
          <button className="icon-btn" title="Restart from beginning" onClick={() => void nova.restart(r.id)}>↩️</button>
        )}
        <button className="icon-btn" title="Remove from list" onClick={() => void remove(false)}>✖️</button>
        {r.state === 'completed' && (
          <button className="icon-btn" title="Delete file from disk" onClick={() => void remove(true)}>🗑️</button>
        )}
      </div>
    </div>
  );
}
