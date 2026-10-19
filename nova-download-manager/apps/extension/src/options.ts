import { getSettings, pairCheck, ping } from './bridgeClient';

const $ = <T extends HTMLElement = HTMLElement>(id: string) => document.getElementById(id) as T;
const CONTENT_ID = 'nova-content';

async function syncDetectionScript(enabled: boolean) {
  try {
    const existing = await chrome.scripting.getRegisteredContentScripts({ ids: [CONTENT_ID] });
    if (enabled && existing.length === 0) {
      await chrome.scripting.registerContentScripts([
        { id: CONTENT_ID, js: ['content.js'], matches: ['*://*/*'], runAt: 'document_idle', persistAcrossSessions: true },
      ]);
    } else if (!enabled && existing.length > 0) {
      await chrome.scripting.unregisterContentScripts({ ids: [CONTENT_ID] });
    }
  } catch (e) {
    $('msg').textContent = `Could not update detection: ${e instanceof Error ? e.message : String(e)}`;
  }
}

async function init() {
  const s = await getSettings();
  ($('token') as HTMLInputElement).value = s.token;
  ($('port') as HTMLInputElement).value = String(s.port);
  ($('autodetect') as HTMLInputElement).checked = s.autoDetect;

  $('save').addEventListener('click', async () => {
    const token = ($('token') as HTMLInputElement).value.trim();
    const port = Math.max(1024, Math.min(65535, parseInt(($('port') as HTMLInputElement).value || '47117', 10)));
    let autoDetect = ($('autodetect') as HTMLInputElement).checked;
    if (autoDetect) {
      // Ask the browser for site access only now that the user opted in.
      const granted = await chrome.permissions.request({ origins: ['*://*/*'] }).catch(() => false);
      if (!granted) {
        autoDetect = false;
        ($('autodetect') as HTMLInputElement).checked = false;
        $('msg').textContent = 'Site access was not granted, so automatic detection stays off. Manual scanning (popup button) still works.';
      }
    } else {
      await chrome.permissions.remove({ origins: ['*://*/*'] }).catch(() => undefined);
    }
    await chrome.storage.local.set({ token, port, autoDetect });
    await syncDetectionScript(autoDetect);
    $('msg').textContent = 'Saved.';
  });

  $('test').addEventListener('click', async () => {
    const settings = {
      token: ($('token') as HTMLInputElement).value.trim(),
      port: parseInt(($('port') as HTMLInputElement).value || '47117', 10),
      autoDetect: false,
    };
    $('msg').textContent = 'Testing…';
    const up = await ping(settings);
    if (!up) { $('msg').textContent = '✗ Nova is not reachable. Start the desktop app and check the port.'; return; }
    const paired = await pairCheck(settings);
    $('msg').textContent = paired.ok ? '✓ Connected and paired with Nova.' : `✗ Nova is running but the token was rejected. Copy it again from Nova → Browser integration.`;
  });
}

document.addEventListener('DOMContentLoaded', () => void init());
