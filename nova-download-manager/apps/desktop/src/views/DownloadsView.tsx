import React from 'react';
import type { DownloadRecord } from '../types';
import { DownloadCard } from '../components/DownloadCard';

interface Props {
  records: DownloadRecord[];
  onToast: (k: 'info' | 'warn' | 'bad', t: string, b?: string) => void;
  onPlay: (r: DownloadRecord) => void;
  onAdd: () => void;
  emptyHint: string;
}

export function DownloadsView({ records, onToast, onPlay, onAdd, emptyHint }: Props) {
  if (records.length === 0) {
    return (
      <div className="empty">
        <div className="big">📥</div>
        <p>{emptyHint}</p>
        <button className="btn primary" onClick={onAdd}>＋ New download</button>
        <p className="small muted" style={{ marginTop: 12 }}>Tip: you can also drag &amp; drop a link into Nova.</p>
      </div>
    );
  }
  return (
    <div className="dl-list">
      {records.map((r) => <DownloadCard key={r.id} record={r} onToast={onToast} onPlay={onPlay} />)}
    </div>
  );
}
