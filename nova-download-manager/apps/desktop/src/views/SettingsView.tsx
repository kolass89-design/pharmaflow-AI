import React, { useState } from 'react';
import type { NovaSettings } from '../types';
import { nova } from '../types';

interface Props {
  settings: NovaSettings;
  save: (patch: Partial<NovaSettings>) => Promise<void>;
  onToast: (k: 'info' | 'warn' | 'bad', t: string, b?: string) => void;
}

function Toggle({ value, onChange }: { value: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="switch">
      <input type="checkbox" checked={value} onChange={(e) => onChange(e.target.checked)} />
      <span className="track" />
    </label>
  );
}

const CATEGORIES = ['video', 'audio', 'documents', 'archives', 'images', 'applications', 'other'];

export function SettingsView({ settings: s, save, onToast }: Props) {
  const [throttle, setThrottle] = useState(s.throttleKBps ? String(s.throttleKBps) : '');

  async function pickDest() {
    const f = await nova.pickFolder();
    if (f) await save({ destDir: f });
  }

  async function pickCategoryDir(cat: string) {
    const f = await nova.pickFolder();
    if (f) await save({ categoryDirs: { ...s.categoryDirs, [cat]: f } });
  }

  return (
    <div>
      <div className="panel">
        <h2>Downloads</h2>
        <div className="setting-row">
          <div>Default download folder<div className="desc mono">{s.destDir}</div></div>
          <button className="btn small" onClick={() => void pickDest()}>Change…</button>
        </div>
        <div className="setting-row">
          <div>Ask for destination every time<div className="desc">Show a folder picker before each manually added download.</div></div>
          <Toggle value={s.askDestinationEachTime} onChange={(v) => void save({ askDestinationEachTime: v })} />
        </div>
        <div className="setting-row">
          <div>Maximum simultaneous downloads<div className="desc">Extra downloads wait in the queue (1–10).</div></div>
          <input className="input num" type="number" min={1} max={10} value={s.maxConcurrent}
            onChange={(e) => void save({ maxConcurrent: Math.max(1, Math.min(10, parseInt(e.target.value || '1', 10))) })} style={{ width: 80, minWidth: 80 }} />
        </div>
        <div className="setting-row">
          <div>Segmented downloading<div className="desc">Split large files into parallel segments when the server supports Range requests. Segments are byte-validated before assembly.</div></div>
          <Toggle value={s.enableSegmented} onChange={(v) => void save({ enableSegmented: v })} />
        </div>
        <div className="setting-row">
          <div>Segments per file<div className="desc">More segments can be faster but load the server more (2–8).</div></div>
          <input className="input num" type="number" min={2} max={8} value={s.maxSegments}
            onChange={(e) => void save({ maxSegments: Math.max(2, Math.min(8, parseInt(e.target.value || '4', 10))) })} style={{ width: 80, minWidth: 80 }} />
        </div>
        <div className="setting-row">
          <div>Bandwidth limit per download (KB/s)<div className="desc">Leave empty for unlimited.</div></div>
          <div className="row" style={{ justifyContent: 'flex-end' }}>
            <input className="input num" type="number" min={16} placeholder="Unlimited" value={throttle} onChange={(e) => setThrottle(e.target.value)} style={{ width: 120, minWidth: 120 }} />
            <button className="btn small" onClick={() => void save({ throttleKBps: throttle ? Math.max(16, parseInt(throttle, 10)) : null })}>Apply</button>
          </div>
        </div>
        <div className="setting-row">
          <div>Keep partial files after cancel<div className="desc">Off (default): canceled downloads delete their .novapart data. On: keep them so a later retry can resume.</div></div>
          <Toggle value={s.keepPartialsOnCancel} onChange={(v) => void save({ keepPartialsOnCancel: v })} />
        </div>
        <h3>Category folders (optional)</h3>
        {CATEGORIES.map((c) => (
          <div className="setting-row" key={c}>
            <div style={{ textTransform: 'capitalize' }}>{c}<div className="desc mono">{s.categoryDirs[c] ?? '— uses default folder'}</div></div>
            <div className="row" style={{ justifyContent: 'flex-end' }}>
              <button className="btn small" onClick={() => void pickCategoryDir(c)}>Set…</button>
              {s.categoryDirs[c] && <button className="btn small" onClick={() => { const next = { ...s.categoryDirs }; delete next[c]; void save({ categoryDirs: next }); }}>Clear</button>}
            </div>
          </div>
        ))}
      </div>

      <div className="panel">
        <h2>Browser integration &amp; detection</h2>
        <div className="setting-row">
          <div>Extension bridge<div className="desc">Local connection (127.0.0.1 only) used by the Nova browser extension. Token-protected; see “Browser integration”.</div></div>
          <Toggle value={s.bridgeEnabled} onChange={(v) => void save({ bridgeEnabled: v })} />
        </div>
        <div className="setting-row">
          <div>Bridge port<div className="desc">Change only if another app uses this port, then update the extension.</div></div>
          <input className="input num" type="number" min={1024} max={65535} value={s.bridgePort}
            onChange={(e) => void save({ bridgePort: Math.max(1024, Math.min(65535, parseInt(e.target.value || '47117', 10))) })} style={{ width: 110, minWidth: 110 }} />
        </div>
        <div className="setting-row">
          <div>Watch clipboard for download links<div className="desc">When you copy a direct file URL, Nova offers to download it. Clipboard contents never leave this computer, and nothing downloads without your click.</div></div>
          <Toggle value={s.clipboardWatch} onChange={(v) => void save({ clipboardWatch: v })} />
        </div>
      </div>

      <div className="panel">
        <h2>Interface &amp; notifications</h2>
        <div className="setting-row">
          <div>Theme</div>
          <select className="input" value={s.theme} onChange={(e) => void save({ theme: e.target.value as NovaSettings['theme'] })}>
            <option value="dark">Dark</option>
            <option value="light">Light</option>
          </select>
        </div>
        <div className="setting-row">
          <div>Desktop notifications<div className="desc">Notify when downloads finish or fail, and when media is detected.</div></div>
          <Toggle value={s.notifications} onChange={(v) => void save({ notifications: v })} />
        </div>
        <div className="setting-row">
          <div>Sound on completion<div className="desc">Plays the system notification sound with the “download complete” notification.</div></div>
          <Toggle value={s.soundOnComplete} onChange={(v) => void save({ soundOnComplete: v })} />
        </div>
        <div className="setting-row">
          <div>Close to system tray<div className="desc">Closing the window keeps Nova downloading in the background. Quit from the tray icon.</div></div>
          <Toggle value={s.closeToTray} onChange={(v) => void save({ closeToTray: v })} />
        </div>
      </div>

      <div className="panel">
        <h2>Privacy &amp; security</h2>
        <div className="setting-row">
          <div>Allow private/local network downloads<div className="desc">Off (default) blocks downloads from localhost and LAN addresses (protects against link-based probing of your network). Turn on only if you download from a trusted local server.</div></div>
          <Toggle value={s.allowPrivateNetwork} onChange={(v) => void save({ allowPrivateNetwork: v })} />
        </div>
        <p>
          Nova collects <b>no telemetry</b>, has no accounts, and stores everything (history, settings, partial files) locally on this
          computer. Downloaded files are <b>never run automatically</b> — programs you download are revealed in their folder so you can
          scan them first. Any file from the internet can be unsafe; keep your antivirus enabled.
        </p>
      </div>

      <div className="panel">
        <h2>Data management</h2>
        <div className="setting-row">
          <div>Clear finished history<div className="desc">Removes completed/failed/canceled entries from the list. Downloaded files stay on disk.</div></div>
          <button className="btn small danger" onClick={async () => { await nova.clearHistory(); onToast('info', 'History cleared'); }}>Clear</button>
        </div>
        <div className="setting-row">
          <div>Clean up orphaned partial files<div className="desc">Deletes leftover .novapart files in the download folder that no tracked download owns.</div></div>
          <button className="btn small" onClick={async () => { const n = await nova.cleanupPartials(); onToast('info', 'Cleanup done', `${n} partial file(s) removed.`); }}>Clean up</button>
        </div>
      </div>

      <div className="panel">
        <h2>About</h2>
        <p>
          <b>Nova Download Manager 0.1.0</b> — a lightweight, privacy-respecting download manager with a built-in media player.
          Downloads use streaming I/O with pause/resume (HTTP Range), optional byte-validated segmented transfers, and
          SHA-256 integrity recording. Open source (MIT). Third-party licenses are listed in the project documentation.
        </p>
      </div>
    </div>
  );
}
