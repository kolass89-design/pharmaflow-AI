import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { Detection, DownloadRecord, NovaSettings, View } from './types';
import { nova, isBrowserPreview } from './types';
import { Overview } from './views/Overview';
import { DownloadsView } from './views/DownloadsView';
import { PlayerView } from './views/PlayerView';
import { IntegrationView } from './views/IntegrationView';
import { SettingsView } from './views/SettingsView';
import { AddDialog } from './components/AddDialog';
import { formatBytes } from './lib/format';

interface Toast { id: number; kind: 'info' | 'warn' | 'bad'; title: string; body?: string; action?: { label: string; run: () => void } }

const NAV: { view: View; label: string; icon: string; section?: string }[] = [
  { view: 'overview', label: 'Overview', icon: '🏠' },
  { view: 'all', label: 'All downloads', icon: '📥', section: 'Library' },
  { view: 'downloading', label: 'Downloading', icon: '⚡' },
  { view: 'queued', label: 'Queued', icon: '🕒' },
  { view: 'completed', label: 'Completed', icon: '✅' },
  { view: 'failed', label: 'Failed', icon: '⚠️' },
  { view: 'video', label: 'Video', icon: '🎬', section: 'Categories' },
  { view: 'audio', label: 'Audio', icon: '🎵' },
  { view: 'documents', label: 'Documents', icon: '📄' },
  { view: 'other', label: 'Other files', icon: '📦' },
  { view: 'player', label: 'Media player', icon: '▶️', section: 'Tools' },
  { view: 'integration', label: 'Browser integration', icon: '🧩' },
  { view: 'settings', label: 'Settings', icon: '⚙️' },
];

const TITLES: Record<View, string> = {
  overview: 'Overview', all: 'All downloads', downloading: 'Downloading', queued: 'Queued', completed: 'Completed',
  failed: 'Failed', video: 'Video', audio: 'Audio', documents: 'Documents', other: 'Other files',
  player: 'Media player', integration: 'Browser integration', settings: 'Settings',
};

export function App() {
  const [view, setView] = useState<View>('overview');
  const [records, setRecords] = useState<DownloadRecord[]>([]);
  const [settings, setSettings] = useState<NovaSettings | null>(null);
  const [query, setQuery] = useState('');
  const [showAdd, setShowAdd] = useState<{ url: string } | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [playRequest, setPlayRequest] = useState<{ path: string; nonce: number } | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const toastId = useRef(0);

  const toast = useCallback((kind: Toast['kind'], title: string, body?: string, action?: Toast['action']) => {
    const id = ++toastId.current;
    setToasts((t) => [...t, { id, kind, title, body, action }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 9000);
  }, []);

  useEffect(() => {
    void nova.listDownloads().then(setRecords).catch(() => undefined);
    void nova.getSettings().then(setSettings).catch(() => undefined);
    void nova.getDetections().then(setDetections).catch(() => undefined);
    const offUpdate = nova.onUpdate((r) => {
      setRecords((prev) => {
        const i = prev.findIndex((x) => x.id === r.id);
        if (i === -1) return [...prev, r];
        const next = [...prev];
        next[i] = r;
        return next;
      });
    });
    const offRemoved = nova.onRemoved((id) => setRecords((prev) => prev.filter((x) => x.id !== id)));
    const offDetection = nova.onDetection((d) => {
      setDetections((prev) => [...prev.filter((x) => x.url !== d.url), d]);
      toast('info', '🎬 Media detected', `${d.fileName ?? d.url}${d.size ? ` · ${formatBytes(d.size)}` : ''}`, {
        label: 'Download',
        run: () => {
          void nova.acceptDetection(d.id);
          setDetections((prev) => prev.filter((x) => x.id !== d.id));
        },
      });
    });
    const offClipboard = nova.onClipboardUrl((url) => {
      toast('info', '📋 Download link copied', url, { label: 'Download…', run: () => setShowAdd({ url }) });
    });
    return () => { offUpdate(); offRemoved(); offDetection(); offClipboard(); };
  }, [toast]);

  useEffect(() => {
    if (settings) document.documentElement.dataset.theme = settings.theme;
  }, [settings]);

  const saveSettings = useCallback(async (patch: Partial<NovaSettings>) => {
    const next = await nova.saveSettings(patch);
    setSettings(next);
  }, []);

  const onPlay = useCallback((r: DownloadRecord) => {
    if (!r.destPath) return;
    setPlayRequest({ path: r.destPath, nonce: Date.now() });
    setView('player');
  }, []);

  const counts = useMemo(() => {
    const c: Partial<Record<View, number>> = {};
    c.all = records.length;
    c.downloading = records.filter((r) => r.state === 'downloading' || r.state === 'probing').length;
    c.queued = records.filter((r) => r.state === 'queued' || r.state === 'paused').length;
    c.completed = records.filter((r) => r.state === 'completed').length;
    c.failed = records.filter((r) => r.state === 'failed').length;
    c.video = records.filter((r) => r.category === 'video').length;
    c.audio = records.filter((r) => r.category === 'audio').length;
    c.documents = records.filter((r) => r.category === 'documents').length;
    c.other = records.filter((r) => !['video', 'audio', 'documents'].includes(r.category)).length;
    return c;
  }, [records]);

  const filtered = useMemo(() => {
    let list = records;
    const q = query.trim().toLowerCase();
    if (q) list = list.filter((r) => r.fileName.toLowerCase().includes(q) || r.url.toLowerCase().includes(q));
    switch (view) {
      case 'all': return list;
      case 'downloading': return list.filter((r) => r.state === 'downloading' || r.state === 'probing');
      case 'queued': return list.filter((r) => r.state === 'queued' || r.state === 'paused');
      case 'completed': return list.filter((r) => r.state === 'completed');
      case 'failed': return list.filter((r) => r.state === 'failed' || r.state === 'canceled');
      case 'video': return list.filter((r) => r.category === 'video');
      case 'audio': return list.filter((r) => r.category === 'audio');
      case 'documents': return list.filter((r) => r.category === 'documents');
      case 'other': return list.filter((r) => !['video', 'audio', 'documents'].includes(r.category));
      default: return list;
    }
  }, [records, view, query]);

  const completedMedia = useMemo(
    () => records.filter((r) => r.state === 'completed' && (r.category === 'video' || r.category === 'audio') && r.destPath),
    [records],
  );

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const text = e.dataTransfer.getData('text/uri-list') || e.dataTransfer.getData('text/plain');
    const url = text.split(/\s+/).find((t) => /^https?:\/\//.test(t));
    if (url) setShowAdd({ url });
    else toast('warn', 'No link found', 'Drop a web link (http/https) to start a download.');
  }

  if (!settings) return <div style={{ padding: 40 }}>Loading Nova…</div>;

  return (
    <div className="app" onDragOver={(e) => { e.preventDefault(); setDragOver(true); }} onDragLeave={() => setDragOver(false)} onDrop={onDrop}>
      <aside className="sidebar">
        <div className="logo">
          <div className="logo-mark">N</div>
          <div><b>Nova</b><span>Download Manager</span></div>
        </div>
        {NAV.map((n) => (
          <React.Fragment key={n.view}>
            {n.section && <div className="nav-label">{n.section}</div>}
            <button className={`nav-item ${view === n.view ? 'active' : ''}`} onClick={() => setView(n.view)}>
              <span>{n.icon}</span> {n.label}
              {counts[n.view] !== undefined && <span className="count">{counts[n.view]}</span>}
              {n.view === 'integration' && detections.length > 0 && <span className="count">{detections.length} new</span>}
            </button>
          </React.Fragment>
        ))}
        <div className="sidebar-foot">
          {isBrowserPreview && (
            <div style={{ background: 'rgba(255,178,36,0.15)', border: '1px solid var(--warn)', borderRadius: 8, padding: '6px 8px', marginBottom: 8, color: 'var(--text)' }}>
              ⚠️ Browser preview with demo data. Install the Nova app for real downloads.
            </div>
          )}
          Drag &amp; drop links anywhere to download.<br />
          Private by design — no accounts, no telemetry.
        </div>
      </aside>

      <div className="main">
        <div className="topbar">
          <h1>{TITLES[view]}</h1>
          <span className="spacer" />
          <input className="search" placeholder="🔍 Search downloads…" value={query} onChange={(e) => setQuery(e.target.value)} />
          <button className="btn" onClick={() => void saveSettings({ theme: settings.theme === 'dark' ? 'light' : 'dark' })} title="Toggle theme">
            {settings.theme === 'dark' ? '☀️' : '🌙'}
          </button>
          <button className="btn primary" onClick={() => setShowAdd({ url: '' })}>＋ New download</button>
        </div>

        <div className="content">
          {dragOver && <div className="empty drag" style={{ marginBottom: 14 }}><div className="big">⬇️</div><p>Drop the link to download it with Nova</p></div>}
          {view === 'overview' && <Overview records={records} onToast={toast} onPlay={onPlay} onAdd={() => setShowAdd({ url: '' })} />}
          {['all', 'downloading', 'queued', 'completed', 'failed', 'video', 'audio', 'documents', 'other'].includes(view) && (
            <DownloadsView
              records={filtered}
              onToast={toast}
              onPlay={onPlay}
              onAdd={() => setShowAdd({ url: '' })}
              emptyHint={query ? `No downloads match “${query}”.` : 'Nothing here yet.'}
            />
          )}
          {view === 'player' && <PlayerView completedMedia={completedMedia} playRequest={playRequest} onToast={toast} />}
          {view === 'integration' && (
            <IntegrationView settings={settings} save={saveSettings} detections={detections} setDetections={setDetections} onToast={toast} />
          )}
          {view === 'settings' && <SettingsView settings={settings} save={saveSettings} onToast={toast} />}
        </div>
      </div>

      {showAdd && (
        <AddDialog initialUrl={showAdd.url} defaultDestDir={settings.destDir} onClose={() => setShowAdd(null)} onToast={toast} />
      )}

      <div className="toasts">
        {toasts.map((t) => (
          <div className={`toast ${t.kind === 'info' ? '' : t.kind}`} key={t.id}>
            <b>{t.title}</b>
            {t.body && <p>{t.body}</p>}
            <div className="row">
              {t.action && <button className="btn small primary" onClick={() => { t.action!.run(); setToasts((x) => x.filter((y) => y.id !== t.id)); }}>{t.action.label}</button>}
              <button className="btn small" onClick={() => setToasts((x) => x.filter((y) => y.id !== t.id))}>Dismiss</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
