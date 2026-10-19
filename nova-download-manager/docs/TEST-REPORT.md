# Nova — Test report

_Last updated: 2026-10-19 (v0.1.0 development). This report states exactly what was executed where — nothing is claimed beyond the evidence._

## Automated suites (run locally + in CI)

| Suite | Tests | Result | What it proves |
|---|---|---|---|
| `@nova/core` — safety | 16 | ✅ pass | URL validation (protocols, private-IP blocking), filename sanitization (traversal, reserved names, length), Content-Disposition parsing, categorization |
| `@nova/core` — engine | 14 | ✅ pass | Byte-exact downloads vs a local fixture server; redirect following; 403/404 handling (no output file); pause→Range-resume (verified via server-side Range log); no-Range server restart; segmented assembly byte-exact + part cleanup; dropped-connection auto-retry+resume; HTTP 429 backoff; truncated transfer **not** marked complete; cancel removes partials |
| `@nova/core` — queue | 8 | ✅ pass | Concurrency-limited completion; duplicate detection + on-disk name de-dup incl. in-flight race; batch parsing with error lines; search; reorder; crash-recovery to *paused*; orphan partial cleanup; unsafe-URL rejection (`file:///`, cloud-metadata IP) |
| `@nova/desktop` — bridge | 9 | ✅ pass | `/ping`; 401 without token; 403 for non-extension origins even *with* token; explicit extension download completes on disk; `detected`+ask doesn't download; `off` refused; domain deny-list; private-URL blocked; `file://` blocked |
| `@nova/extension` — detection | 7 | ✅ pass | Direct media found in `<video>/<audio>/<source>/<a>`; relative URLs resolved; `blob:` (MSE) ignored; `.m3u8/.mpd` classified streaming; images/tracking ignored; de-duplication; extensionless URLs never guessed |
| **Total** | **54** | ✅ **all passing** | Runtime ~8 s locally |

Bugs found *by* these tests during development (fixed + re-tested): premature-close stream hang (moved to `stream.pipeline`), filename race between concurrent downloads, fixture server Range edge cases.

## Build verification

| Artifact | Built where | Evidence |
|---|---|---|
| Core `dist/` (tsc strict) | Local | clean compile |
| Desktop renderer + main bundles | Local | Vite build 189 KB JS (60 KB gzip); `tsc` strict clean (renderer + electron) |
| Extension `nova-extension.zip` | Local | 14,644 bytes, contents verified (`unzip -l`) |
| Windows NSIS + portable | **CI (windows-latest)** | _see CI run artifacts — sizes appended below after first green run_ |
| Linux AppImage + tar.gz | **CI** | same |
| Android APK + AAB | **CI (SDK 34, Gradle 8.9)** | same |

> Local packaging of Electron/Android binaries was **not possible in the development sandbox**: the Electron runtime and Android SDK are fetched from hosts unreachable there (GitHub release-asset CDN / Google). Packaging therefore runs in GitHub Actions. GUI execution on a physical Windows PC/Android phone has **not** been performed yet — items are marked 🟡 in FEATURE-MATRIX.md accordingly.

## Manual / still to verify on real devices (checklist for 0.1.x)

- [ ] Install NSIS build on Windows 10 & 11; SmartScreen wording; uninstall cleanup
- [ ] Portable EXE first-run; tray/close-to-tray; notifications; clipboard watch
- [ ] Real download from a public Range-capable server (e.g. a Linux ISO mirror) incl. network drop mid-file
- [ ] Extension load in Chrome + Edge; pairing flow; scan a page with a direct MP4 (e.g. W3Schools/Google sample buckets); confirm a YouTube page correctly yields “no direct media”
- [ ] APK sideload on Android 10/13/14; share-sheet flow from a browser; background download with app swiped away; battery-saver behavior
- [ ] Player: MP4 (H.264), WebM, MP3 on both platforms; MKV/HEVC error path
- [ ] Large-file (≥2 GB) segmented download memory profile on desktop
- [ ] Disk-full and permission-denied scenarios on both platforms

## Measured (local, this dev machine)

- Core test-suite wall time: ~7 s (38 tests incl. 1.5 MB segmented transfer)
- Renderer production bundle: 189.36 KB minified / 59.85 KB gzip; CSS 12.21 KB / 3.28 KB gzip
- Extension package: 14.6 KB zipped (all scripts minified)
- Engine: streaming with 64 KB buffers — memory is O(connections), not O(file size)

## CI results

_Pending first run — this section is updated with the workflow URL, per-job status, and artifact names/sizes from the Actions API._
