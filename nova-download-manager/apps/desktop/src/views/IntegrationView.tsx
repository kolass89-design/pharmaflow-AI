import React, { useEffect, useState } from 'react';
import type { Detection, NovaSettings } from '../types';
import { nova } from '../types';
import { formatBytes, timeAgo } from '../lib/format';

interface Props {
  settings: NovaSettings;
  save: (patch: Partial<NovaSettings>) => Promise<void>;
  detections: Detection[];
  setDetections: React.Dispatch<React.SetStateAction<Detection[]>>;
  onToast: (k: 'info' | 'warn' | 'bad', t: string, b?: string) => void;
}

export function IntegrationView({ settings, save, detections, setDetections, onToast }: Props) {
  const [bridge, setBridge] = useState<{ enabled: boolean; port: number; token: string; lastSeenAt: number | null } | null>(null);
  const [showToken, setShowToken] = useState(false);

  useEffect(() => {
    void nova.getBridgeInfo().then(setBridge).catch(() => undefined);
  }, [settings.bridgeEnabled, settings.bridgePort, settings.bridgeToken]);

  async function copy(text: string, label: string) {
    try {
      await navigator.clipboard.writeText(text);
      onToast('info', `${label} copied`);
    } catch {
      onToast('warn', 'Copy failed', 'Select the text and copy it manually.');
    }
  }

  async function regenerate() {
    if (!window.confirm('Generate a new pairing token? You will need to paste it into the extension again.')) return;
    const token = await nova.regenerateBridgeToken();
    setBridge((b) => (b ? { ...b, token } : b));
    onToast('info', 'New token generated', 'Update it in the extension settings.');
  }

  async function accept(d: Detection) {
    const r = await nova.acceptDetection(d.id);
    setDetections((prev) => prev.filter((x) => x.id !== d.id));
    if (r.ok) onToast('info', 'Download started', d.fileName ?? d.url);
    else onToast('bad', 'Could not start download', r.message);
  }

  async function dismiss(d: Detection) {
    await nova.dismissDetection(d.id);
    setDetections((prev) => prev.filter((x) => x.id !== d.id));
  }

  return (
    <div>
      <div className="panel">
        <h2>Nova browser extension (Chrome / Edge / Chromium)</h2>
        <p>
          The extension adds a <b>“Download with Nova”</b> action to your browser and can spot <b>direct media files</b> on
          pages you visit. It talks to this app only through a local bridge on <span className="mono">127.0.0.1</span> protected
          by a pairing token — nothing is sent to any server, and no browsing history is collected.
        </p>
        <div className="setting-row">
          <div>
            Bridge status
            <div className="desc">
              {bridge?.enabled ? `Listening on 127.0.0.1:${bridge.port}` : 'Disabled in Settings'}
              {bridge?.lastSeenAt ? ` · extension last seen ${timeAgo(bridge.lastSeenAt)}` : ' · extension not connected yet'}
            </div>
          </div>
          <span className={`chip ${bridge?.enabled ? 'completed' : 'failed'}`}>{bridge?.enabled ? 'Active' : 'Off'}</span>
        </div>
        <div className="setting-row">
          <div>
            Pairing token
            <div className="desc">Paste this into the extension’s settings once. Treat it like a password — anyone with it (and access to this computer) could queue downloads.</div>
          </div>
          <div className="row" style={{ justifyContent: 'flex-end' }}>
            <code className="token">{showToken ? bridge?.token ?? '…' : '••••••••••••••••••••••••'}</code>
            <button className="btn small" onClick={() => setShowToken((s) => !s)}>{showToken ? 'Hide' : 'Show'}</button>
            <button className="btn small" onClick={() => bridge && void copy(bridge.token, 'Token')}>Copy</button>
            <button className="btn small" onClick={() => void regenerate()}>Regenerate</button>
          </div>
        </div>
        <h3>Install the extension</h3>
        <ol className="steps">
          <li>Get the extension package (<span className="mono">nova-extension.zip</span>) from the Nova release page and unzip it.</li>
          <li>In Chrome open <span className="mono">chrome://extensions</span> (Edge: <span className="mono">edge://extensions</span>) and enable <b>Developer mode</b>.</li>
          <li>Click <b>Load unpacked</b> and select the unzipped folder.</li>
          <li>Open the extension’s options, paste the pairing token above, and click <b>Test connection</b>.</li>
        </ol>
        <h3>Permissions the extension requests — and why</h3>
        <table className="matrix">
          <thead><tr><th>Permission</th><th>Why Nova needs it</th></tr></thead>
          <tbody>
            <tr><td className="mono">activeTab + scripting</td><td>When you click the Nova button, inspect the current page for direct media files (video/audio tags pointing at real files).</td></tr>
            <tr><td className="mono">contextMenus</td><td>Adds “Download with Nova” / “Send link to Nova” to the right-click menu.</td></tr>
            <tr><td className="mono">storage</td><td>Stores your pairing token and preferences locally in the browser.</td></tr>
            <tr><td className="mono">host: 127.0.0.1</td><td>Talks to the Nova desktop app on this computer only.</td></tr>
            <tr><td className="mono">optional: all sites (detection)</td><td>Only if you enable automatic detection: a lightweight scanner looks for direct media files on pages you open. It never reads page text, passwords or history, and sends candidates only to your own Nova app.</td></tr>
          </tbody>
        </table>
      </div>

      <div className="panel">
        <h2>Automatic media detection</h2>
        <p>
          When the extension finds a <b>direct</b> media file on a page (for example an MP4 hosted as a plain file), Nova can
          react in one of three ways. Streaming sites that use adaptive/encrypted players (most large video platforms) do not
          expose direct files — Nova does not scrape streams, extract cookies, or bypass DRM/paywalls. For those, use the
          site’s own download/offline features.
        </p>
        <div className="setting-row">
          <div>When media is detected<div className="desc">Default is “Ask me” — nothing downloads without your confirmation.</div></div>
          <select className="input" value={settings.detectMode} onChange={(e) => void save({ detectMode: e.target.value as NovaSettings['detectMode'] })}>
            <option value="off">Off — manual only</option>
            <option value="ask">Ask me before downloading</option>
            <option value="auto">Download automatically (opt-in)</option>
          </select>
        </div>
        <div className="setting-row">
          <div>Never detect on these domains<div className="desc">One hostname per line, e.g. example.com</div></div>
          <button className="btn small" onClick={() => {
            const v = window.prompt('Domains where detection is disabled (one per line):', settings.detectDenyList.join('\n'));
            if (v !== null) void save({ detectDenyList: v.split('\n').map((s) => s.trim().toLowerCase()).filter(Boolean) });
          }}>Edit list ({settings.detectDenyList.length})</button>
        </div>
      </div>

      <div className="panel">
        <h2>Detected media awaiting your confirmation ({detections.length})</h2>
        {detections.length === 0 && <p className="muted">Nothing waiting. Detected direct media files will appear here (and as a pop-up) when “Ask me” is selected.</p>}
        <div className="dl-list">
          {detections.map((d) => (
            <div className="dl-card" key={d.id}>
              <div className="dl-icon">{(d.mime ?? '').startsWith('audio') ? '🎵' : '🎬'}</div>
              <div className="dl-main">
                <div className="dl-name">{d.fileName ?? 'Media file'}</div>
                <div className="dl-meta">
                  {d.size ? <span>{formatBytes(d.size)}</span> : null}
                  {d.mime ? <span>{d.mime}</span> : null}
                  {d.pageUrl ? <span>from {new URL(d.pageUrl).hostname}</span> : null}
                  <span>{timeAgo(d.at)}</span>
                </div>
                <div className="dl-url">{d.url}</div>
              </div>
              <div className="dl-actions">
                <button className="btn small primary" onClick={() => void accept(d)}>Download</button>
                <button className="btn small" onClick={() => void dismiss(d)}>Dismiss</button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="panel">
        <h2>What about YouTube, Facebook, TikTok…?</h2>
        <table className="matrix">
          <thead><tr><th>Source type</th><th>Nova behavior</th></tr></thead>
          <tbody>
            <tr><td>Direct media files (plain .mp4/.mp3 links, files on open servers, sample/lecture sites)</td><td>✅ Detected and downloadable, with size/format shown before you confirm.</td></tr>
            <tr><td>Sites with an official download/offline feature</td><td>↗ Use the site’s own feature — Nova won’t interfere. You can still send ordinary file links to Nova manually.</td></tr>
            <tr><td>Adaptive streams (HLS/DASH) exposed to the browser</td><td>⚠️ Not treated as files. Nova does not assemble streaming manifests into downloads unless a direct file is offered.</td></tr>
            <tr><td>DRM-encrypted, paywalled, or login-only media</td><td>🚫 Never bypassed. No DRM circumvention, no cookie/session extraction, no hidden endpoints.</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
