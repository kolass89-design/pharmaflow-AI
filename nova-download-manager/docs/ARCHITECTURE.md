# Nova — Architecture

## Overview

```
┌────────────────────┐      127.0.0.1 bridge (token)     ┌─────────────────────────┐
│ Chromium extension │ ────────────────────────────────▶ │ Desktop app (Electron)  │
│ detect / menus /   │                                   │ main: engine+bridge+IPC │
│ popup              │ ◀────── detections (ask mode) ───│ renderer: React UI      │
└────────────────────┘                                   │ player: nova-media://   │
                                                         └──────────┬──────────────┘
┌────────────────────┐                                              │ uses
│ Android app        │                                   ┌──────────▼──────────────┐
│ Kotlin engine      │  (same semantics, native impl.)   │ @nova/core (TypeScript) │
│ OkHttp + Compose   │                                   │ probe/resume/segments/  │
│ Media3 player      │                                   │ queue/safety/persistence│
└────────────────────┘                                   └─────────────────────────┘
```

## Why these technologies

| Piece | Choice | Rationale |
|---|---|---|
| Shared engine | TypeScript, zero runtime dependencies (Node `http`/`fs`/`stream`) | One stream-tested implementation; runs in the desktop main process; unit/integration tests need no network. Pure logic is portable to a future Tauri/Rust host. |
| Desktop shell | Electron + React/Vite | The only stack that produces a real **Windows NSIS installer + portable EXE** from CI/Linux without a Rust or Windows-SDK toolchain. Electron is heavier than Tauri; mitigated by a lean renderer (60 KB gzip), single-instance, tray mode, and streaming I/O (no whole-file buffering). The engine/UI split keeps a Tauri migration feasible. |
| Extension | MV3, esbuild-bundled | Minimal permissions; content script registered dynamically only when the user opts into detection. |
| Android | Kotlin + Compose + OkHttp + Media3 | Native performance and lifecycle behavior; no cross-platform runtime tax. The Kotlin engine mirrors core semantics (Range resume, validation, categories, safety). |
| Persistence | Local JSON files (atomic write-rename), no DB server | Local-first, tiny footprint, crash-safe enough, zero ops. |
| Backend | **None** | Updates ship via GitHub Releases. No account system, no proxy downloads, no telemetry endpoint → minimal attack surface and zero running cost. |

## Download engine (`packages/core`)

- **Probe:** `HEAD` (fallback: ranged GET) → filename (Content-Disposition/URL), size, MIME, Range support, redirect chain (every hop re-validated).
- **Single-stream:** `stream.pipeline` to `<file>.novapart`, resume appends with `Range`; a `200` answer to a Range request restarts cleanly; `416`+full-size short-circuits to finalize.
- **Segmented:** ≥8 MB and Range-capable → up to N parallel ranges, each to its own part file; byte-tiling is validated (no gaps/overlaps) before streaming assembly. Segment state persists in `<file>.nova-meta.json` for cross-restart resume.
- **Finalize:** byte-count must equal the server-declared size; SHA-256 computed (and verified when the server publishes `x-checksum-sha256`); atomic rename into place. Failures keep the partial for resume and never produce a fake "completed" file.
- **Retries:** transient errors (network, 429, 5xx) retry ≤3× with exponential backoff honoring `Retry-After`, resuming when possible. 401/403/404 fail fast with plain-language messages (no auth bypass attempts).
- **Queue:** concurrency slots, ordering, scheduling (`scheduledAt`), duplicate detection, per-category folders, filename de-duplication against disk **and** in-flight records, orphan-partial cleanup, debounced persistence.
- **Throttle:** per-download KB/s pacing transform.

## Browser bridge security model

`127.0.0.1`-only HTTP listener; per-install 192-bit pairing token (constant-time compare) required for mutations; CORS answers only `*-extension://` origins; 64 KB payload cap; every URL re-validated by the engine (incl. private-network blocking). `/ping` reveals presence only. See [SECURITY.md](SECURITY.md).

## Media playback

- Desktop: files are served to the sandboxed renderer through a privileged `nova-media://<token>` protocol with HTTP Range support (seekable, streamed, allowlisted by token — renderer never gets raw filesystem access).
- Android: Media3/ExoPlayer plays from app storage or user-picked `content://` URIs.

## Data locations

- Windows: `%APPDATA%\@nova\desktop\` (settings/history/player), downloads default to the OS Downloads folder.
- Android: app-internal `files/downloads` (+ published copy in `Download/Nova` via MediaStore), history at `files/downloads.json`, partials in `cache/parts`.

## Resource profile

Bounded buffers everywhere (64 KB), no whole-file RAM loads, debounced UI updates (≤~7/s/task), lazy renderer views. Measured locally: renderer bundle 189 KB (60 KB gzip); extension package 14.6 KB. Package size/memory of packaged apps are measured in CI — see TEST-REPORT.md.
