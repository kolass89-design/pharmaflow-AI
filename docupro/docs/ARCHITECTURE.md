# Architecture

## Overview

DOCUPRO is three deployable pieces built from one repository:

```
┌──────────────────────────────────────────────────────────────────┐
│ Browser / PWA            Windows shell        Android app        │
│ React + TypeScript  ◄──  Tauri v2 (WebView2)  Tauri v2 (WebView) │
└───────────────┬──────────────────────────────────────────────────┘
                │  HTTPS, multipart upload, JSON polling
┌───────────────▼──────────────────────────────────────────────────┐
│ FastAPI service (one process)                                    │
│  ├─ catalog router     /api/tools, /api/capabilities, /health    │
│  ├─ jobs router        create, poll, cancel, delete, download    │
│  ├─ rate limiter       token bucket per client address           │
│  ├─ job manager        in-memory registry + on-disk job folders  │
│  └─ sweeper thread     retention, orphans, cancellation          │
└───────────────┬──────────────────────────────────────────────────┘
                │  one short-lived OS process per conversion
┌───────────────▼──────────────────────────────────────────────────┐
│ Worker process                                                   │
│  manifest.json → registry → engine → output/artifact-aN          │
│  JSON-lines progress on stdout, hard CPU/file-size rlimits       │
└───────────────┬──────────────────────────────────────────────────┘
                │
   MuPDF · pdf2docx · python-docx · Pillow · pillow-heif · openpyxl
   Tesseract or RapidOCR · LibreOffice (optional)
```

## Why a process per conversion

* **Real timeouts.** A thread cannot be interrupted while a C library is
  working; a process can be terminated, and the job manager also enforces a
  wall-clock deadline from the parent.
* **Crash isolation.** A malformed file that segfaults a parser takes down one
  worker, not the service.
* **Memory reclamation.** Memory used by a 300-page PDF is returned to the OS
  when the worker exits.
* **Cancellation.** `POST /api/jobs/{id}/cancel` terminates the process and
  removes the job directory immediately.

The trade-off is that job state lives in the service process. DOCUPRO therefore
runs a single uvicorn worker and provides concurrency through
`DOCUPRO_MAX_CONCURRENCY` (default 2). Scaling horizontally would require a
shared job store; the code is deliberately kept free of that dependency.

## Job lifecycle

```
reserve ──► upload ──► queued ──► running ──► succeeded ──► downloaded ──► expired
                                     │
                                     ├──► failed (inputs deleted)
                                     └──► cancelled (everything deleted)
```

1. `POST /api/jobs` validates the tool, options and file signatures, streams
   uploads to a private directory while enforcing per-file and per-job limits.
2. The manager writes `manifest.json` (paths, options, limits) and spawns
   `python -m docupro_api.worker <job_dir>` with a sanitised environment.
3. The worker emits JSON lines: `{"type":"progress"}`, `{"type":"result"}` or
   `{"type":"error"}`. The parent clamps progress to 0.99 until the result is
   validated.
4. The worker renames every output to `artifact-aN`, checks it is non-empty and
   inside the output directory, then reports it. The parent re-checks existence
   and size before the job becomes downloadable.
5. Inputs are deleted as soon as the conversion succeeds. Outputs are deleted
   after `DOCUPRO_RETENTION_MINUTES` (30), or 120 s after the last artifact has
   been downloaded (`DOCUPRO_DELETE_AFTER_DOWNLOAD_SECONDS`).

## Engines

| Area | Library | Notes |
| --- | --- | --- |
| PDF parsing, rendering, edit | PyMuPDF | page selection, raster output, watermark, numbering, encryption |
| PDF → Word | pdf2docx | layout analysis; ligature normalisation afterwards |
| PDF → Word fallback / scan | PyMuPDF text + OCR | reconstructs paragraphs from line boxes |
| Word → PDF | LibreOffice, else built-in | HTML + PyMuPDF Story, with header/footer stamping |
| Word → text/HTML | python-docx / mammoth | reading order follows the document body |
| Images | Pillow, pillow-heif | HEIC/HEIF decoding, EXIF orientation, alpha flattening |
| Spreadsheets | openpyxl | Excel → CSV and a real table-layout PDF renderer |
| OCR | Tesseract, else RapidOCR | 12 language choices; automatic fallback |
| Office conversion | LibreOffice | PPTX → PDF, `.doc` → PDF, Excel → PDF |
| Text/HTML → PDF | PyMuPDF Story | sanitised HTML subset, no scripts or remote fetches |

Optional engines are detected at runtime. `GET /api/capabilities` reports what
the running server can do, and unavailable tools are marked in the catalog
instead of being advertised.

## Conversion registry

`engines/registry.py` is the single source of truth. Each `ConversionSpec`
declares:

* identifiers, category, title, description, keywords
* accepted input extensions and the kinds that must be detected
* output kind, extension and media type
* option schema (type, default, bounds, choices, `advanced` flag)
* file count limits, batching/zip behaviour, estimated duration
* the engine callable and an availability check
* user-facing limitations

`GET /api/tools` serialises this registry, `scripts/export_catalog.py` writes a
reviewable contract to `packages/shared/catalog.json`, and CI fails if the two
drift apart.

## Storage

```
$DOCUPRO_DATA_DIR/jobs/<32-hex job id>/
    input/     uploads (deleted on success, failure or cancellation)
    work/      scratch space for the engine
    output/    artifact-a1, artifact-a2, ...
    manifest.json
```

Directories are created with mode `0700`. Filenames from users are never used on
disk: uploads are stored as `input-0001.<ext>` and artifacts as `artifact-aN`.
The download name is a sanitised version of the user's original name.

## Web client

* React 18 + TypeScript strict mode, Vite, Tailwind CSS 3.
* Eight routes: home, all tools, tool detail, recent, settings, privacy, about,
  not found. Deep links are served by the API's SPA fallback.
* The catalog is fetched at start-up and cached in `localStorage`; tool pages
  render their option form from the server schema, so a new engine option needs
  no front-end change.
* Uploads use `XMLHttpRequest` for real upload progress; job state is polled
  every 0.9 s with abort support.
* Conversion history, theme and preferences stay in `localStorage`. History is
  optional and can be cleared or disabled.
* PWA: manifest, maskable icons, offline app shell. API responses are never
  cached.

## Desktop and mobile shell

`apps/desktop` is a Tauri v2 project shared by Windows and Android. It adds:

* native Save As through `tauri-plugin-dialog` and `tauri-plugin-fs`
  (the browser build falls back to a blob download),
* native drag-and-drop and the Android file picker through the standard file
  input,
* a strict content security policy and a minimal permission set,
* Windows installers (NSIS + MSI) and Android APK/AAB targets.

The shell does not bundle the conversion engines; it talks to a DOCUPRO service
over HTTPS. The service URL is a build-time variable (`VITE_API_BASE`) and a
runtime setting.
