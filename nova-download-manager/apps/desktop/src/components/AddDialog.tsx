import React, { useState } from 'react';
import { nova } from '../types';
import type { ProbeResult } from '../types';
import { formatBytes } from '../lib/format';

interface Props {
  initialUrl?: string;
  defaultDestDir: string;
  onClose: () => void;
  onToast: (kind: 'info' | 'warn' | 'bad', title: string, body?: string) => void;
}

export function AddDialog({ initialUrl = '', defaultDestDir, onClose, onToast }: Props) {
  const [tab, setTab] = useState<'single' | 'batch'>('single');
  const [url, setUrl] = useState(initialUrl);
  const [fileName, setFileName] = useState('');
  const [destDir, setDestDir] = useState(defaultDestDir);
  const [startNow, setStartNow] = useState(true);
  const [schedule, setSchedule] = useState('');
  const [batchText, setBatchText] = useState('');
  const [probe, setProbe] = useState<ProbeResult | null>(null);
  const [probeError, setProbeError] = useState('');
  const [busy, setBusy] = useState(false);

  async function doProbe() {
    setProbe(null);
    setProbeError('');
    if (!url.trim()) return;
    setBusy(true);
    try {
      const p = await nova.probe(url.trim());
      setProbe(p);
      if (!fileName) setFileName(p.fileName);
    } catch (e) {
      setProbeError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function pickFolder() {
    const f = await nova.pickFolder();
    if (f) setDestDir(f);
  }

  async function submit() {
    setBusy(true);
    try {
      if (tab === 'batch') {
        const { added, errors } = await nova.addBatch(batchText, { destDir, startNow });
        const real = added.filter((a) => !a.duplicate).length;
        const dups = added.length - real;
        onToast(errors.length ? 'warn' : 'info', 'Batch processed',
          `${real} added${dups ? `, ${dups} duplicates skipped` : ''}${errors.length ? `, ${errors.length} invalid: ${errors.map((e) => e.line).join(', ')}` : ''}`);
        onClose();
        return;
      }
      const scheduledAt = schedule ? new Date(schedule).getTime() : undefined;
      const res = await nova.add(url.trim(), {
        destDir,
        fileName: fileName.trim() || undefined,
        startNow: scheduledAt ? false : startNow,
        scheduledAt,
      });
      if (res.duplicate) {
        onToast('warn', 'Duplicate download', `"${res.record.fileName}" is already in your list. It was not added again.`);
      } else {
        onToast('info', 'Download added', res.record.fileName);
      }
      onClose();
    } catch (e) {
      onToast('bad', 'Could not add download', e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Add download</h2>
        <div className="tabs">
          <button className={tab === 'single' ? 'on' : ''} onClick={() => setTab('single')}>Single URL</button>
          <button className={tab === 'batch' ? 'on' : ''} onClick={() => setTab('batch')}>Batch (multiple URLs)</button>
        </div>

        {tab === 'single' ? (
          <>
            <div className="field">
              <label>File URL (HTTP / HTTPS)</label>
              <div className="row">
                <input type="url" placeholder="https://example.com/file.mp4" value={url} onChange={(e) => setUrl(e.target.value)} onBlur={() => void doProbe()} autoFocus />
                <button className="btn" onClick={() => void doProbe()} disabled={busy || !url.trim()}>Check</button>
              </div>
            </div>
            {busy && <p className="muted small">Contacting server…</p>}
            {probeError && <div className="probe-box" style={{ color: 'var(--bad)' }}>{probeError}<br /><span className="muted">You can still queue it — Nova will report the server error when it tries.</span></div>}
            {probe && (
              <div className="probe-box">
                <div>📄 <b>{probe.fileName}</b></div>
                <div className="muted">
                  Size: {formatBytes(probe.totalBytes)}{probe.mime ? ` · ${probe.mime}` : ''} ·{' '}
                  {probe.supportsRange ? '✅ Server supports pause/resume' : '⚠️ Server does not support resume — pausing will restart this download'}
                </div>
                {probe.finalUrl !== url.trim() && <div className="muted small">Redirects to: {probe.finalUrl}</div>}
              </div>
            )}
            <div className="field" style={{ marginTop: 12 }}>
              <label>Save as</label>
              <input type="text" value={fileName} onChange={(e) => setFileName(e.target.value)} placeholder="File name (auto-detected)" />
            </div>
            <div className="field">
              <label>Start at (optional schedule)</label>
              <input type="datetime-local" value={schedule} onChange={(e) => setSchedule(e.target.value)} />
            </div>
          </>
        ) : (
          <div className="field">
            <label>One URL per line</label>
            <textarea value={batchText} onChange={(e) => setBatchText(e.target.value)} placeholder={'https://example.com/a.zip\nhttps://example.com/b.pdf'} autoFocus />
          </div>
        )}

        <div className="field">
          <label>Destination folder</label>
          <div className="row">
            <input type="text" value={destDir} onChange={(e) => setDestDir(e.target.value)} />
            <button className="btn" onClick={() => void pickFolder()}>Browse…</button>
          </div>
        </div>
        <label className="check">
          <input type="checkbox" checked={startNow} onChange={(e) => setStartNow(e.target.checked)} disabled={!!schedule} />
          <span>Start downloading immediately{schedule ? ' (disabled — scheduled)' : ''}</span>
        </label>

        <div className="modal-actions">
          <button className="btn" onClick={onClose}>Cancel</button>
          <button className="btn primary" onClick={() => void submit()} disabled={busy || (tab === 'single' ? !url.trim() : !batchText.trim())}>
            {tab === 'batch' ? 'Add all' : 'Add download'}
          </button>
        </div>
      </div>
    </div>
  );
}
