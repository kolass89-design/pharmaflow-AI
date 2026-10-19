# DOCUPRO — Delivery report

**Date:** 2026-10-19 · **Version:** 1.0.0 · **Branch:** `arena/ff1487be-pharmaflow-ai`
**Repository:** <https://github.com/kolass89-design/pharmaflow-AI> (public, `main`)
**Product root in repository:** [`docupro/`](../)

Every claim below is tied to a command that was executed in this environment or
to a file in the repository. Where something could **not** be built or deployed
here, it says so explicitly and gives the exact reason. No URL in this document
is invented: the only deployment URLs mentioned are the ones you will create.

---

## A. Summary

DOCUPRO is a complete document conversion product:

| Deliverable | State |
| --- | --- |
| Conversion API (37 tools, 6 categories) | **Delivered, tested, running** |
| Web application (React 18 + TS + Vite + Tailwind) | **Delivered, type-checked, built, UI-tested** |
| Windows / Android shell (Tauri v2, native dialogs) | **Source complete, buildable; no binary built here** (no Rust/Java/Windows toolchain in this sandbox) |
| Container image | **Dockerfile complete; not built here** (no Docker daemon in this sandbox) |
| CI / release pipelines | **Written and versioned in `ci/workflows/`; cannot be pushed to `.github/workflows` with this token** |
| Live public deployment | **Not done**: needs your hosting account or a repository secret. The deploy workflow and its end-to-end verifier (12/12 checks against a real server) are proven locally |
| Documentation (14 documents) | **Delivered** |
| Measured performance report | **Delivered**, 15 measured scenarios |

Verified locally, end to end: **98 automated tests pass**, **36 of 37 conversions
verified with real output files**, the web client builds to **≈98 KB gzipped** (89.4 kB JS + 8.3 kB CSS)
and completes a real upload → convert → download flow in a DOM test.

---

## B. What was built

### B.1 Conversion engine — 37 tools

| Category | Tools |
| --- | --- |
| PDF (19) | PDF → Word, JPEG, PNG, text, Excel, searchable PDF, single-page PDFs; extract images; merge; split; extract pages; delete pages; reorder; rotate; compress; watermark; page numbers; protect (AES-256); unlock |
| Word (5) | Word → PDF, JPEG, PNG, text, HTML |
| Image (7) | images → PDF (multi-file, page size, orientation, margins, fit); format conversion (JPEG/PNG/WebP/HEIC/GIF/BMP/TIFF); resize; compress; rotate; image → text (OCR); image → Word |
| Other (6) | Excel → PDF; Excel → CSV; CSV → Excel; PowerPoint → PDF (LibreOffice); text/Markdown → PDF; HTML → PDF |

Design decisions that shaped the result:

* **One registry** (`services/api/docupro_api/engines/registry.py`) declares
  inputs, outputs, option schema, limitations and availability for every tool.
  The API, the web client and the desktop shell all read the same catalog, so an
  unavailable engine (e.g. PowerPoint without LibreOffice) is shown as
  *unavailable with a reason* instead of failing after a 40 MB upload.
* **One OS process per conversion** for real timeouts, cancellation, crash
  isolation and memory reclamation — no broker, no database.
* **No third-party conversion API**, no account, no AI features, no telemetry.
* **Documents are deleted**, and the interface says so at every step.

### B.2 Web application

Eight routes (`/`, `/tools`, `/tool/:toolId`, `/recent`, `/settings`,
`/privacy`, `/about`, `*`), generated from the server catalog:

* drag-and-drop, paste and keyboard file selection, with client-side validation
  before an upload starts;
* multi-file tools with reordering (merge, images → PDF) and per-file removal;
* option forms generated from the schema (select, number, boolean, text,
  password, page ranges) with advanced options collapsed;
* real upload progress (XHR), job progress with elapsed time and cancel;
* result list with preview (PDF/image/text), permission-checked download,
  native share on mobile, expiry countdown and **Delete now**;
* human error messages mapped from server error codes, with recovery actions;
* light/dark/system theme with no flash, focus rings, skip link, ARIA live
  regions and reduced-motion support;
* installable PWA with offline app shell (API traffic is never cached);
* history and preferences stored only in the browser, and deletable.

### B.3 Native shells

`apps/desktop` (Tauri v2) targets Windows (NSIS + MSI + portable exe) and
Android (APK + AAB). It is not a WebView screenshot wrapper: it adds native Save
As (`tauri-plugin-dialog` + `tauri-plugin-fs`), a strict CSP, a minimal
permission allow-list, and it consumes the same bundle as the web app. The
browser path falls back to a normal download when the shell is absent.

### B.4 Operations

Multi-stage `Dockerfile` (Node build → non-root Python runtime with Tesseract,
fonts and optional LibreOffice), `docker-compose.yml` with sandboxing and
healthcheck, `render.yaml`, `fly.toml`, `deploy/docupro.service` (systemd
hardening) and `deploy/Caddyfile`. `.env.example` documents every setting.

---

## C. Verification evidence

All commands were run in this environment on 2026-10-19.

### C.1 Static checks

```text
$ ruff check .                 All checks passed!
$ ruff format --check .        31 files already formatted
$ npx tsc --noEmit             (no output — success)
```

### C.2 Backend tests

```text
$ python -m pytest -q
100 passed, 1 warning in 18.67s

$ python -m pytest -q --cov=docupro_api --cov-report=term
TOTAL   3604   823   77%
```

Coverage is 77% of statements. `worker.py` shows 0% because it executes as a
subprocess that coverage cannot instrument; its behaviour is exercised by every
end-to-end job test.

Test files: `test_security.py`, `test_engines.py`, `test_api.py` (catalog,
headers, lifecycle, token enforcement, spoofed/executable/corrupted uploads,
wrong passwords, ordering, cancellation, deletion, expiry sweep, rate limiting,
four concurrent jobs, artifact-name opacity, retention shortening).

### C.3 Conversion matrix

```text
$ python scripts/verify_engines.py tests/corpus/generated
36/37 passed, 0 failed, 1 skipped, 0 unavailable
```

Sample of the printed evidence (each row is a real file whose bytes were
validated — PDF page count, DOCX openability, image decoding, non-empty size):

```text
pdf-to-word          pass  0.44s  report-fr.docx (41 KB)
pdf-to-searchable    pass  2.32s  scan-fr-searchable.pdf (426 KB)
pdf-to-excel         pass  0.1s   report-fr-tables.xlsx (6 KB)
word-to-pdf          pass  0.1s   report.pdf (475 KB)
image-to-word        pass  0.74s  ocr-sample.docx (35 KB)
excel-to-pdf         pass  0.02s  workbook.pdf (90 KB)
html-to-pdf          pass  0.01s  page.pdf (87 KB)
powerpoint-to-pdf    skipped       requires LibreOffice
```

`powerpoint-to-pdf` is skipped **because LibreOffice is not installed in this
sandbox** and cannot be installed (no root/apt). The code path is exercised by
CI, where the runner installs LibreOffice; do not claim it verified until that
run exists.

### C.4 Web client

```text
$ npx tsc --noEmit                 success (strict mode, noUnusedLocals)
$ npm run build
dist/assets/index-*.js         134 551 B │ gzip 34.30 kB
dist/assets/react-*.js         164 086 B │ gzip 53.56 kB
dist/assets/index-*.css         48 399 B │ gzip  8.39 kB
✓ built in 2.84s

Total including lazy chunks: JS 89.4 kB gzipped, CSS 8.3 kB gzipped
(measured by gzipping the emitted files; asset hashes change on every build).
```

UI tests (jsdom, against the live production server):

```text
SMOKE_REPORT {"hasHero":true,"hasDropzoneLabel":true,"toolLinks":9,
 "toolHeading":"PDF to Word","toolHasOptions":true,"toolHasLimitations":true,
 "toolHasInputs":1,"toolsPage":true,"privacyPage":true}

FLOW_REPORT {"rendered":true,"toolLoaded":true,"fileAttached":true,
 "fileListed":true,"submitClicked":true,"progressShown":true,"succeeded":true,
 "artifactShown":true,"downloadButton":true,"historyRecorded":true,
 "errorShown":true,"noDownloadOnError":true}
```

The flow test attaches a real PDF to the file input, clicks **Convert now**,
waits for the worker, checks the artifact and the recorded history, then repeats
with a corrupted PDF and asserts an error is shown **and** that no download is
offered.

### C.5 Live HTTP session

```text
GET  /                     200 text/html
GET  /tool/pdf-to-word     200 text/html   (SPA deep link)
GET  /api/tools            37 tools, 36 available
POST /api/jobs             202  (pdf-to-word)
GET  /api/jobs/<id>        succeeded, 1 artifact, 42 073 B
GET  ...?token=…           200, 42 073 B, valid DOCX (18 entries, testzip None)
GET  ... (no token)        404
```

### C.6 Performance (measured, see [PERFORMANCE.md](PERFORMANCE.md))

2 vCPU / 3.9 GB container, 50-page PDF: text extraction **352 pages/s**
(0.142 s), rasterisation at 150 dpi **11.6 pages/s** (4.31 s), layout-preserving
PDF → Word **9.2 pages/s** (5.41 s); OCR **2.1 s/page**; Word → PDF **0.11 s**.
Peak RSS per conversion 69–648 MB. Raw data:
[`performance-results.json`](performance-results.json).

---

## D. Artifacts produced

| Artifact | Location | Status |
| --- | --- | --- |
| Source (service, web, shell, docs, CI) | repository `docupro/` | **committed** |
| Production web bundle | `apps/desktop` → `apps/web/dist` (build output, not committed) | **built here** |
| Catalog contract | `packages/shared/catalog.json` (37 tools) | **committed** |
| Icons (web + Windows + Android) | `apps/web/public/icons`, `apps/desktop/src-tauri/icons` | **generated here** |
| Backend automated tests | `services/api/tests` | **98 passing** |
| Conversion verification report | this document, §C.3 | **measured** |
| Performance report | `docs/PERFORMANCE.md` + JSON | **measured** |
| Windows installer (.exe/.msi) | produced by `release.yml` on `windows-latest` | **not built** (no Rust/Windows toolchain here) |
| Android APK/AAB | produced by `release.yml` on `ubuntu-latest` | **not built** (no JDK/Android SDK here) |
| Container image | `Dockerfile`; published to GHCR by `release.yml` | **not built** (no Docker daemon here) |

Honest statement: **no installer, APK, AAB, container image or public URL exists
yet.** The pipelines that create them are written and committed, but this
environment cannot execute them and the GitHub token cannot push them to
`.github/workflows` (see §H.1). Anything else would be a fabricated claim.

---

## E. Deployment

**Status: prepared, not deployed.** There is no hosting credential for this
project in this environment, so no public URL exists to report.

Two supported paths, both one command once you supply the account:

1. **Render** — `render.yaml` blueprint (Docker, 1 GB disk, health check
   `/api/health`). Set the `RENDER_DEPLOY_HOOK_URL` and `DOCUPRO_PUBLIC_URL`
   repository secrets, then run the Deploy workflow; its last step executes
   `scripts/smoke_deploy.py` against the real URL (health, catalog, conversion,
   token enforcement, deletion). That run is the evidence a deployment works.
2. **Any VPS** — `docker compose up -d --build` behind `deploy/Caddyfile`
   (automatic HTTPS), or `deploy/docupro.service` + Caddy.

`scripts/smoke_deploy.py http://127.0.0.1:8000` was executed against the local
production server (built client + API) and passed **12/12 checks, 0 failures**:

```text
PASS  health                       {'status': 'ok', 'version': '1.0.0'}
PASS  security headers
PASS  catalog                      36/37 available
PASS  capabilities                 MuPDF, pdf2docx, rapidocr, openpyxl
PASS  web client served            1736 bytes
PASS  job accepted
PASS  job succeeded
PASS  artifact size                36824
PASS  download                     36824 bytes
PASS  download is not cacheable
PASS  token required              404
PASS  delete on request           expired

0 failure(s)
```

The same script is the final step of the Deploy workflow, so the verification
path a real deployment must pass is proven end to end.

---

## F. Security and privacy

Implemented and tested (details in [SECURITY.md](SECURITY.md), [PRIVACY.md](PRIVACY.md)):

* signature validation of every upload (a PDF that is really an executable is
  rejected with 415), filename sanitisation, no user-controlled paths;
* isolated worker per conversion with CPU/file-size rlimits, 240 s wall clock,
  process kill on cancel, output confined to `output/`;
* OOXML zip-bomb limits (5 000 entries / 300 MB), 80 MP image cap, 500-page cap;
* download tokens: job ID alone returns 404; the token never appears in logs,
  the catalog or the history;
* rate limiting (40/min, burst 20) with `Retry-After`, queue cap, 30-minute
  retention, immediate delete-on-request, sweeper, orphan cleanup on restart;
* security headers (CSP, nosniff, no-referrer, permissions policy, HSTS behind
  TLS), API `no-store`, closed CORS by default;
* container: non-root, read-only rootfs, `no-new-privileges`, all capabilities
  dropped, pids/memory/CPU limits;
* no accounts, no cookies, no analytics, no third-party calls, no training on
  user documents.

Not covered: DDoS at the network layer, and vulnerabilities inside the parsing
libraries themselves (mitigated by process isolation; `security.yml` runs
`pip-audit`/`npm audit` weekly).

---

## G. Known limitations

Full list: [LIMITATIONS.md](LIMITATIONS.md). The ones that matter most:

1. **PowerPoint → PDF and legacy `.doc` need LibreOffice.** Not installable
   here → not verified here. The container installs it by default; without it
   the tool is marked unavailable rather than failing.
2. **Word → PDF without LibreOffice** uses the built-in renderer: headings,
   tables, images, page breaks, headers/footers and page numbers are preserved,
   but exact Word pagination and advanced constructs (text boxes, SmartArt,
   equations) are simplified. The UI states this on the tool page.
3. **PDF → Word** is best for text-based PDFs; complex multi-column layouts are
   approximated. Scanned PDFs use OCR (no original formatting).
4. **PDF → Excel** detects tables geometrically; borderless/merged tables may be
   imperfect. It returns `no_tables` instead of an empty workbook.
5. **Compression** only resizes images; text-only PDFs barely shrink.
6. **HTML → PDF** sanitises input (no scripts, no remote assets).
7. Single-process job registry: scale vertically (`DOCUPRO_MAX_CONCURRENCY`),
   not with replicas.
8. Interface is English-only; no formal WCAG audit has been performed.

Resolved during this work (previously open):

* presentation ligatures (`ﬁ`, `ﬀ`) are now normalised in PDF → text and
  PDF → Word output, so extracted text is searchable;
* the duplicate-section defect in the DOCX fixture was a fixture bug (the
  generator repeated the same section); the fixture now produces distinct
  annexes and the renderer output matches the source;
* the download-retention grace period was a hard-coded `120`; it is now
  `DOCUPRO_DELETE_AFTER_DOWNLOAD_SECONDS` (default 120, `0` disables) and is
  covered by a test;
* the artifact download path silently fell back to "any file in the output
  directory"; it now returns 404 for an unknown artifact ID, covered by a test;
* deleting or expiring a job left an empty per-job directory (with only
  `manifest.json`) behind for the lifetime of the service; terminal states now
  remove the whole job directory, covered by two tests.

---

## H. Open items and how to finish them

### H.1 GitHub Actions cannot be enabled from this session

`git push` of any `.github/workflows/*` file is rejected by GitHub:

```text
! [remote rejected] … (refusing to allow a GitHub App to create or update
workflow `.github/workflows/probe.yml` without `workflows` permission)
```

The GitHub App token used here has no `workflows` scope, and
`GET /repos/.../actions/permissions` returns **403**. The pipelines are therefore
committed under `ci/workflows/` (`ci.yml`, `release.yml`, `deploy.yml`,
`security.yml`) with a helper:

```bash
docupro/scripts/install_workflows.sh
git add .github/workflows && git commit -m "ci: activate pipelines" && git push
```

(A token or collaborator with the `workflow` scope is required.)

### H.2 Native artifacts

Run once on a machine (or after enabling `release.yml`):

```bash
cd docupro/apps/web && npm ci && npm run build
cd ../desktop && npm install
npm run build:windows           # needs Rust + VS Build Tools on Windows
npx tauri android init --ci && npx tauri android build --apk --aab --ci
```

The `release` workflow does this on `windows-latest` and `ubuntu-latest` with
JDK 17 + NDK 26, publishes the container to GHCR and attaches the artifacts with
`SHA256SUMS.txt` to a GitHub release. Signing keys are optional secrets; nothing
secret is committed.

### H.3 Public deployment

Create the Render blueprint (or a VPS with the compose file), add
`RENDER_DEPLOY_HOOK_URL` + `DOCUPRO_PUBLIC_URL`, run the Deploy workflow, and
paste the output of `scripts/smoke_deploy.py` into this report. Until then the
project has **no public URL** and this report does not claim one.

### H.4 Repository

* Repo creation of the preferred private `docupro-converter` failed
  (`createRepository` not accessible to this token), so the work lives in the
  existing `kolass89-design/pharmaflow-AI` repository under `docupro/`.
* Branch `arena/ff1487be-pharmaflow-ai` is pushed and a pull request to `main`
  is open: <https://github.com/kolass89-design/pharmaflow-AI/pull/1>. Merge it
  when you are ready; nothing is merged automatically.
