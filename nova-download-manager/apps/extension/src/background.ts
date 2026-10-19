import { classifyUrl, fileNameOf, type MediaCandidate } from './detect';
import { getSettings, sendToNova } from './bridgeClient';

const MENU_LINK = 'nova-download-link';
const MENU_MEDIA = 'nova-download-media';
const MENU_PAGE = 'nova-download-page';

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({ id: MENU_LINK, title: 'Download link with Nova', contexts: ['link'] });
  chrome.contextMenus.create({ id: MENU_MEDIA, title: 'Download media with Nova', contexts: ['video', 'audio'] });
  chrome.contextMenus.create({ id: MENU_PAGE, title: 'Send this page URL to Nova', contexts: ['page'] });
});

async function notify(tabId: number | undefined, ok: boolean, message: string) {
  try {
    await chrome.action.setBadgeText({ tabId, text: ok ? '✓' : '!' });
    await chrome.action.setBadgeBackgroundColor({ tabId, color: ok ? '#2fd08c' : '#ff5d73' });
    setTimeout(() => void chrome.action.setBadgeText({ tabId, text: '' }).catch(() => undefined), 3500);
  } catch {
    /* badge is best-effort */
  }
  if (tabId !== undefined) {
    void chrome.tabs.sendMessage(tabId, { type: 'nova:toast', ok, message }).catch(() => undefined);
  }
}

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const target = info.menuItemId === MENU_LINK ? info.linkUrl : info.menuItemId === MENU_MEDIA ? info.srcUrl : info.pageUrl ?? tab?.url;
  if (!target) return;
  const cls = classifyUrl(target);
  if (cls === 'streaming-manifest') {
    await notify(tab?.id, false, 'This is a streaming playlist (HLS/DASH), not a direct file. Nova does not scrape streams — use the site’s official download/offline option if available.');
    return;
  }
  if (cls === 'invalid') {
    await notify(tab?.id, false, 'That is not a downloadable web link.');
    return;
  }
  const result = await sendToNova({
    kind: 'download',
    url: target,
    fileName: cls === 'page' ? undefined : fileNameOf(target),
    pageTitle: tab?.title,
    pageUrl: tab?.url,
  });
  await notify(tab?.id, result.ok, result.message);
});

// Per-tab detected candidates (for badge + popup), forwarded per Nova's detect mode.
const perTab = new Map<number, MediaCandidate[]>();

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!msg || typeof msg !== 'object') return;
  const m = msg as { type?: string; candidates?: MediaCandidate[]; payload?: { url: string; fileName?: string; mime?: string }; pageUrl?: string };

  if (m.type === 'nova:detected' && sender.tab?.id !== undefined && Array.isArray(m.candidates)) {
    const tabId = sender.tab.id;
    perTab.set(tabId, m.candidates);
    void (async () => {
      const s = await getSettings();
      if (m.candidates!.length > 0) {
        await chrome.action.setBadgeText({ tabId, text: String(m.candidates!.length) }).catch(() => undefined);
        await chrome.action.setBadgeBackgroundColor({ tabId, color: '#6d7cff' }).catch(() => undefined);
        if (s.autoDetect && s.token) {
          // Forward as passive detections; Nova decides (ask/auto/off) and dedupes.
          for (const c of m.candidates!) {
            void sendToNova({ kind: 'detected', url: c.url, fileName: c.fileName, mime: c.mimeGuess, pageTitle: sender.tab?.title, pageUrl: sender.tab?.url }, s);
          }
        }
      } else {
        await chrome.action.setBadgeText({ tabId, text: '' }).catch(() => undefined);
      }
    })();
    return;
  }

  if (m.type === 'nova:getCandidates' && typeof (m as { tabId?: number }).tabId === 'number') {
    sendResponse({ candidates: perTab.get((m as { tabId: number }).tabId) ?? [] });
    return true;
  }

  if (m.type === 'nova:download' && m.payload?.url) {
    void sendToNova({ kind: 'download', url: m.payload.url, fileName: m.payload.fileName, mime: m.payload.mime, pageUrl: m.pageUrl }).then((r) => {
      sendResponse(r);
    });
    return true; // async response
  }
});

chrome.tabs.onRemoved.addListener((tabId) => perTab.delete(tabId));
chrome.tabs.onUpdated.addListener((tabId, info) => {
  if (info.status === 'loading') {
    perTab.delete(tabId);
    void chrome.action.setBadgeText({ tabId, text: '' }).catch(() => undefined);
  }
});
