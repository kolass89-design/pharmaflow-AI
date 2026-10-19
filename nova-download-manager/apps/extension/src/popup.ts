import { classifyUrl, fileNameOf, type MediaCandidate } from './detect';
import { getSettings, ping, sendToNova } from './bridgeClient';

const $ = <T extends HTMLElement = HTMLElement>(id: string) => document.getElementById(id) as T;

async function activeTab(): Promise<chrome.tabs.Tab | undefined> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

function renderCandidates(list: MediaCandidate[], pageUrl?: string) {
  const box = $('candidates');
  box.innerHTML = '';
  if (!list.length) {
    box.innerHTML = '<p class="muted">No direct media files found on this page. Streaming players (blob/HLS/DASH) are not downloadable files — look for the site’s official download option.</p>';
    return;
  }
  for (const c of list) {
    const row = document.createElement('div');
    row.className = 'cand';
    row.innerHTML = `<div class="ic">${c.kind === 'audio' ? '🎵' : '🎬'}</div>
      <div class="meta"><div class="nm"></div><div class="sub"></div></div>`;
    row.querySelector('.nm')!.textContent = c.fileName;
    row.querySelector('.sub')!.textContent = `${c.mimeGuess || c.kind} · size checked in Nova before download`;
    const btn = document.createElement('button');
    btn.className = 'btn primary';
    btn.textContent = 'Download';
    btn.addEventListener('click', async () => {
      btn.disabled = true;
      btn.textContent = 'Sending…';
      const r = await sendToNova({ kind: 'download', url: c.url, fileName: c.fileName, mime: c.mimeGuess, pageUrl });
      btn.textContent = r.ok ? '✓ Sent' : 'Retry';
      if (!r.ok) { btn.disabled = false; $('status').textContent = r.message; }
    });
    row.appendChild(btn);
    box.appendChild(row);
  }
}

async function scanCurrentTab() {
  const tab = await activeTab();
  if (!tab?.id) return;
  $('candidates').innerHTML = '<p class="muted">Scanning page…</p>';
  try {
    await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ['scan.js'] });
    const [res] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => (window as unknown as { __novaScan?: () => MediaCandidate[] }).__novaScan?.() ?? [],
    });
    renderCandidates((res?.result as MediaCandidate[]) ?? [], tab.url);
  } catch {
    $('candidates').innerHTML = '<p class="muted">This page cannot be scanned (browser-internal page or blocked by the site).</p>';
  }
}

async function init() {
  const settings = await getSettings();
  const tab = await activeTab();
  const online = await ping(settings);
  $('dot').className = `dot ${online ? 'on' : 'off'}`;
  $('status').textContent = online
    ? settings.token ? 'Nova is running and paired.' : 'Nova is running — paste your pairing token in Settings.'
    : 'Nova is not running. Start the desktop app first.';

  // If the current tab itself is a direct file, offer it.
  if (tab?.url) {
    const cls = classifyUrl(tab.url);
    if (cls === 'direct-file' || cls === 'direct-video' || cls === 'direct-audio') {
      const row = $('pagefile');
      row.style.display = 'block';
      $('pagefile-name').textContent = fileNameOf(tab.url);
      $('pagefile-btn').addEventListener('click', async () => {
        const r = await sendToNova({ kind: 'download', url: tab.url!, fileName: fileNameOf(tab.url!), pageUrl: tab.url });
        $('status').textContent = r.message;
      });
    }
  }

  // Candidates already noticed by the content script (if auto-detect enabled).
  if (tab?.id !== undefined) {
    const resp = await chrome.runtime.sendMessage({ type: 'nova:getCandidates', tabId: tab.id }).catch(() => null) as { candidates?: MediaCandidate[] } | null;
    if (resp?.candidates?.length) renderCandidates(resp.candidates, tab.url);
  }

  $('scan').addEventListener('click', () => void scanCurrentTab());
  $('options').addEventListener('click', () => void chrome.runtime.openOptionsPage());
  $('sendpage').addEventListener('click', async () => {
    if (!tab?.url) return;
    const r = await sendToNova({ kind: 'download', url: tab.url, pageTitle: tab.title, pageUrl: tab.url });
    $('status').textContent = r.message;
  });
}

document.addEventListener('DOMContentLoaded', () => void init());
