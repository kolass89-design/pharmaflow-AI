import { findDirectMedia } from './detect';

/**
 * Passive detection content script. Registered dynamically ONLY after the
 * user enables "Automatic media detection" in the extension options (which
 * triggers the browser's host-permission prompt). It looks only for direct
 * media-file URLs in media/link elements — it never reads page text, form
 * data, or anything else, and it talks only to the extension itself.
 */
let lastSignature = '';
let timer: number | undefined;

function scan() {
  try {
    const candidates = findDirectMedia(document, location.href);
    const sig = candidates.map((c) => c.url).join('|');
    if (sig !== lastSignature) {
      lastSignature = sig;
      void chrome.runtime.sendMessage({ type: 'nova:detected', candidates }).catch(() => undefined);
    }
  } catch {
    /* never break the page */
  }
}

function debouncedScan() {
  if (timer) window.clearTimeout(timer);
  timer = window.setTimeout(scan, 700);
}

scan();
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', scan);
const observer = new MutationObserver(debouncedScan);
observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['src', 'href'] });

// Small in-page toast for context-menu feedback.
chrome.runtime.onMessage.addListener((msg) => {
  if (!msg || (msg as { type?: string }).type !== 'nova:toast') return;
  const { ok, message } = msg as { ok: boolean; message: string };
  const el = document.createElement('div');
  el.textContent = `${ok ? '✓' : '⚠'} Nova: ${message}`;
  el.style.cssText =
    'position:fixed;right:16px;bottom:16px;z-index:2147483647;max-width:360px;background:#101831;color:#e8ecf8;' +
    'border:1px solid #24305c;border-left:4px solid ' + (ok ? '#2fd08c' : '#ffb224') +
    ';border-radius:10px;padding:10px 12px;font:13px system-ui,sans-serif;box-shadow:0 10px 30px rgba(0,0,0,.4)';
  document.documentElement.appendChild(el);
  setTimeout(() => el.remove(), 6000);
});
