# Nova browser extension — install & use

Works in Chrome, Edge, Brave and other Chromium browsers (Manifest V3). The extension only makes sense together with the Nova desktop app.

## Install

1. Download `nova-extension.zip` from the Release page (or build it: `npm run zip -w @nova/extension`) and unzip it to a permanent folder.
2. Open `chrome://extensions` (Edge: `edge://extensions`).
3. Enable **Developer mode** (top-right).
4. Click **Load unpacked** → select the unzipped folder.
5. Start Nova on your computer, go to **Browser integration**, and copy the **pairing token**.
6. Click the Nova toolbar icon → **Settings**, paste the token, **Save**, then **Test connection** → “Connected and paired”.

## Use

- **Toolbar popup:** *Scan this page for media* lists direct video/audio files on the page — each with a Download button. If the tab itself is a file, it's offered directly.
- **Right-click:** *Download link/media with Nova* on any link, video or audio.
- **Automatic detection (optional):** enable it in the extension settings (the browser will ask for site access). Nova then shows a badge count on pages with direct media and forwards candidates to the desktop app, which follows your setting there: **Ask me** (default), **Auto-download** (opt-in), or **Off**. You can exclude specific domains inside Nova.
- **Privacy:** detection looks only at media/link URLs. No page text, no history, no cookies — and everything goes only to your own computer (`127.0.0.1`), protected by the pairing token.

## What you can expect on popular sites

- Sites that host actual files (many universities, podcast feeds, file hosts, sample libraries): ✅ detected and downloadable.
- YouTube/TikTok/Facebook/etc.: these use adaptive streaming (not plain files) and their terms prohibit third-party downloading. Nova will find **nothing to download** there and won't try to work around it. Use the platforms' official offline features (e.g. YouTube Premium downloads, "Save video" where offered).
- If a page uses a streaming playlist (`.m3u8`/`.mpd`), Nova labels it as streaming instead of pretending it's a file.

## Troubleshooting

- **“Nova is not running”** — start the desktop app; check the bridge is enabled (Nova → Settings → Browser integration).
- **Token rejected** — re-copy it from Nova → Browser integration (regenerate if needed) and make sure the port matches in both places (default 47117).
- **Nothing detected on a page with a player** — the player is likely streaming via `blob:`/HLS/DASH. That is a technical and legal boundary Nova respects.
