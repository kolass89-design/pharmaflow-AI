import React from 'react';
import type { DownloadRecord } from '../types';
import { DownloadCard } from '../components/DownloadCard';
import { formatBytes, formatSpeed } from '../lib/format';

interface Props {
  records: DownloadRecord[];
  onToast: (k: 'info' | 'warn' | 'bad', t: string, b?: string) => void;
  onPlay: (r: DownloadRecord) => void;
  onAdd: () => void;
}

export function Overview({ records, onToast, onPlay, onAdd }: Props) {
  const active = records.filter((r) => r.state === 'downloading' || r.state === 'probing');
  const completed = records.filter((r) => r.state === 'completed');
  const failed = records.filter((r) => r.state === 'failed');
  const totalSpeed = active.reduce((a, r) => a + r.speedBps, 0);
  const totalDownloaded = completed.reduce((a, r) => a + (r.totalBytes ?? r.downloadedBytes), 0);
  const recent = [...records].sort((a, b) => b.updatedAt - a.updatedAt).slice(0, 5);

  return (
    <div>
      <div className="stats">
        <div className="stat"><div className="k">Downloading now</div><div className="v">{active.length}</div><div className="s">{formatSpeed(totalSpeed)} combined</div></div>
        <div className="stat"><div className="k">Completed</div><div className="v">{completed.length}</div><div className="s">{formatBytes(totalDownloaded)} saved</div></div>
        <div className="stat"><div className="k">In queue</div><div className="v">{records.filter((r) => r.state === 'queued').length}</div><div className="s">waiting for a free slot</div></div>
        <div className="stat"><div className="k">Failed</div><div className="v">{failed.length}</div><div className="s">need attention</div></div>
        <div className="stat"><div className="k">All time</div><div className="v">{records.length}</div><div className="s">downloads tracked</div></div>
      </div>

      <div className="panel">
        <h2>Quick start</h2>
        <p>
          Paste any direct file link (HTTP/HTTPS), drop a link anywhere in this window, or send downloads from your
          browser with the Nova extension. Nova resumes interrupted downloads automatically when the server supports it,
          and never marks a partial file as finished.
        </p>
        <button className="btn primary" onClick={onAdd}>＋ New download</button>
      </div>

      <h3 style={{ margin: '4px 0 12px', color: 'var(--muted)', textTransform: 'uppercase', fontSize: 12.5, letterSpacing: 0.8 }}>Recent activity</h3>
      {recent.length === 0 ? (
        <div className="empty"><div className="big">🌌</div><p>Nothing here yet — add your first download.</p></div>
      ) : (
        <div className="dl-list">
          {recent.map((r) => <DownloadCard key={r.id} record={r} onToast={onToast} onPlay={onPlay} />)}
        </div>
      )}
    </div>
  );
}
