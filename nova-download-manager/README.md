# ⬇️ Nova Download Manager

A premium, lightweight, privacy-respecting download manager for **Windows** and **Android**, with a **Chromium browser extension** and a **built-in media player**. No accounts. No telemetry. No ads. Your downloads stay on your device.

![status](https://img.shields.io/badge/version-0.1.0-blue) ![license](https://img.shields.io/badge/license-MIT-green)

## What Nova does

- **Real download engine** — streaming HTTP/HTTPS downloads with pause/resume (HTTP Range), automatic retries with backoff, optional byte-validated **segmented** (multi-connection) downloads, redirect handling, bandwidth limiting, scheduling, and size + SHA-256 integrity recording. A partial file is **never** marked as complete.
- **Queue management** — concurrency limits, reorder, batch add, duplicate warnings, categories (Video / Audio / Documents / Archives / Images / Applications), per-category folders, search & filters, history.
- **Automatic media detection (honest edition)** — the browser extension finds **direct** media files on pages and offers them in Nova. It does **not** scrape streaming sites, extract cookies, or bypass DRM/paywalls — see [the compatibility matrix](docs/FEATURE-MATRIX.md).
- **Built-in player** — play MP4/WebM/MP3/M4A/OGG/WAV (platform codecs), playlists, seek/volume/speed/fullscreen, resume-position memory, keyboard shortcuts (Windows), touch controls (Android). Works with files already on your device.
- **Private by design** — local-only storage, no telemetry, token-paired loopback-only browser bridge, downloaded programs are never auto-run.

## Get Nova

> Builds are produced by GitHub Actions. Windows installers are **unsigned** unless a code-signing certificate is configured (Windows SmartScreen may warn — choose “More info → Run anyway” only if you trust the source, i.e. this repo’s Releases). Android CI builds are **debug-signed** unless a release keystore is configured via secrets (fine for sideload testing, not for Play Store).

- **Windows 10/11:** `Nova Download Manager Setup *.exe` (installer) or `NovaDownloadManager-*-portable.exe` from the **Releases** page / CI artifacts.
- **Android:** `app-release.apk` (install directly) or `app-release.aab` (Play Console upload).
- **Browser extension:** `nova-extension.zip` — see [docs/EXTENSION-GUIDE.md](docs/EXTENSION-GUIDE.md).
- **Linux:** AppImage / tar.gz are also produced by CI.

## Repository layout

```
packages/core/     Shared TypeScript download engine (queue, resume, segments) + tests
apps/desktop/      Electron app (Windows/Linux): engine host, tray, bridge, React UI
apps/extension/    Chromium MV3 extension (detection, context menus, popup)
apps/android/      Native Android app (Kotlin, Compose, OkHttp engine, Media3 player)
docs/              Architecture, feature matrix, security, build & test docs
site/              Static product page (deployable to GitHub Pages)
```

## Develop

Prereqs: Node ≥ 20 (desktop/core/extension), JDK 17 + Android SDK (Android), Gradle 8.9.

```bash
npm install
npm run build -w @nova/core     # engine
npm test                        # core (38) + desktop bridge (9) + extension (7) tests
npm run build -w @nova/desktop  # renderer + electron bundles
npm run zip -w @nova/extension  # -> apps/extension/nova-extension.zip
cd apps/android && gradle assembleRelease bundleRelease
```

Packaging (needs network for the Electron runtime — use CI or a normal dev machine):

```bash
npm run dist:win -w @nova/desktop     # NSIS installer + portable exe
npm run dist:linux -w @nova/desktop   # AppImage + tar.gz
```

See [docs/BUILD.md](docs/BUILD.md) for signing, CI secrets, and troubleshooting.

## Move this project to its own repository

This project was developed inside a monorepo folder. To spin it out:

```bash
gh repo create nova-download-manager --private
cd nova-download-manager
git init && git add -A && git commit -m "Nova Download Manager 0.1.0"
git remote add origin https://github.com/<you>/nova-download-manager.git
git push -u origin main
# then: git tag v0.1.0 && git push origin v0.1.0   (triggers release.yml)
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) · [Feature matrix](docs/FEATURE-MATRIX.md) · [Security](docs/SECURITY.md)
- [Build from source](docs/BUILD.md) · [Extension guide](docs/EXTENSION-GUIDE.md) · [Test report](docs/TEST-REPORT.md) · [Licensing](docs/LICENSING.md)

## License

MIT. Third-party notices: [docs/LICENSING.md](docs/LICENSING.md). Nova is an original product; it is not affiliated with Internet Download Manager.
