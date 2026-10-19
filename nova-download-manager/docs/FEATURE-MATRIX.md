# Nova — Feature matrix & honest compatibility

Legend: ✅ implemented & tested · 🟡 implemented, environment-tested only (e.g. build-verified by CI, needs a device) · ⛔ intentionally not supported · 🔜 planned

## Download engine

| Feature | Desktop | Android | Notes |
|---|---|---|---|
| Direct HTTP/HTTPS downloads | ✅ | 🟡 | Streaming; byte-exact in tests |
| Filename/size/type detection | ✅ | 🟡 | HEAD → ranged-GET probe fallback |
| Pause / resume | ✅ | 🟡 | Range resume; non-Range servers flagged in UI, restart on retry |
| Cancel (+ partial cleanup setting) | ✅ | 🟡 | |
| Retry with backoff (network/429/5xx) | ✅ | 🔜 manual retry | Android: tap Retry (resume-aware); auto-retry planned |
| Segmented parallel download | ✅ | ⛔ | Desktop ≥8 MB, byte-tiling validated. Skipped on Android (battery/wifi fairness) |
| Redirects (re-validated per hop) | ✅ | 🟡 | OkHttp follows; initial URL validated |
| Size integrity check | ✅ | 🟡 | Incomplete files are never marked complete |
| SHA-256 | ✅ | 🟡 | Verified when server publishes checksum header (desktop) |
| Queue + concurrency limit | ✅ | 🟡 | 1–10 desktop, 1–5 Android |
| Reorder queue | ✅ | 🔜 | |
| Scheduling | ✅ | 🔜 | |
| Batch add (URL list) | ✅ | 🟡 | |
| Duplicate warnings | ✅ | 🟡 | |
| Categories + category folders | ✅ | 🟡 (categories) | |
| Search / filters | ✅ | 🟡 | |
| Bandwidth limit | ✅ per-download | 🔜 | |
| Speed / avg / ETA | ✅ | 🟡 | |
| Orphan partial cleanup | ✅ | — | Android partials live in cache (OS-managed) |

## Platform integration

| Feature | Status |
|---|---|
| Windows NSIS installer / portable EXE | 🟡 built by CI (unsigned) |
| Linux AppImage | 🟡 built by CI |
| Android APK / AAB | 🟡 built by CI (debug-signed unless keystore secret set) |
| Android share sheet ("Share → Nova") | 🟡 |
| Android foreground-service downloads + notifications | 🟡 |
| Desktop notifications / tray / close-to-tray | ✅ code, 🟡 device-verified |
| Clipboard watch (opt-in, ask-first) | ✅ code |
| Drag & drop URLs (desktop) | ✅ code |
| `nova://add?url=` deep links (Windows) | ✅ code |
| Start on OS login | 🔜 (easy add: Electron `setLoginItemSettings`) |

## Media detection (browser extension)

| Source type | Behavior | Status |
|---|---|---|
| Direct media files (`<video>`/`<audio>`/links to .mp4/.mp3/…) | Detected, listed with type; desktop probes real size/format before download | ✅ logic tested |
| Manual "Download with Nova" (popup/context menu) | Sends link/file URL to Nova (explicit user action) | ✅ bridge tested |
| Detection modes | Off / Ask (default) / Auto (explicit opt-in), per-domain deny list | ✅ tested (bridge) |
| HLS/DASH manifests (.m3u8/.mpd) | Classified as *streaming* — **not** downloaded; UI explains | ✅ |
| `blob:`/MSE players (e.g. most of YouTube) | Not a file; never scraped | ⛔ by design |
| YouTube / TikTok / Facebook / Instagram downloads | **Not supported.** These platforms use adaptive streaming and their terms prohibit third-party downloading. Nova does not extract stream URLs, use cookies/sessions, or hard-code unofficial endpoints. Use each platform's official offline/download features. | ⛔ by design |
| DRM / paywall / login-only media | Never bypassed | ⛔ by design |
| Multiple quality variants (360p/720p…) | Shown **only** when the page itself exposes multiple direct files (each is listed individually). Nova never invents resolutions and never renames extensions to fake a conversion | ✅ |
| Audio extraction / transcoding | 🔜 Not in 0.1. If added, FFmpeg-based (LGPL build) and presented as a separate, explicit step | 🔜 |

## Media player

| Capability | Desktop (Chromium) | Android (Media3) |
|---|---|---|
| Play local MP4 / WebM / MP3 / M4A / OGG / WAV | ✅ code | 🟡 |
| Play existing local files (no download) | ✅ | 🟡 |
| Seek / volume / fullscreen (desktop) / speed | ✅ | 🟡 (speed buttons; fullscreen via player) |
| Playlist + prev/next | ✅ | 🟡 (tap-to-play list) |
| Resume position | ✅ per file | 🔜 |
| Keyboard shortcuts | ✅ Space/arrows/F/M/N/P | n/a |
| Unsupported codec | Clear error naming supported formats | Same |
| MKV/AVI/HEVC | ⚠️ depends on OS codecs; **not guaranteed** — use VLC for exotic files | Media3 handles many; device-dependent |

## Security & privacy

| Measure | Status |
|---|---|
| HTTPS supported; TLS errors surfaced, not silently accepted | ✅ |
| Private/local-network URL blocking (opt-out setting) | ✅ tested |
| Path-traversal-safe filenames (incl. Windows reserved names) | ✅ tested |
| No auto-run of downloaded executables | ✅ |
| Token-paired, loopback-only browser bridge; extension-origin-only CORS | ✅ tested |
| Minimal extension permissions (host access only on explicit opt-in) | ✅ |
| No telemetry / accounts / browsing-history access | ✅ by design |
| Signed Windows binaries / Play signing | 🔜 needs certificates (CI secrets supported) |

Anything marked 🟡 above has **not** been run on a physical Windows PC/Android phone in this development round — it is compile- and CI-verified. See TEST-REPORT.md for precisely what was executed where.
