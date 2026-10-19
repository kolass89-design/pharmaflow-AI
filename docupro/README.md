# DOCUPRO — Smart Document Converter

A complete, self-hostable document conversion product: a premium responsive web
application, a hardened conversion API with 37 tools, and a shared shell for
Windows and Android.

Everything runs on your own infrastructure. There is no account system, no
database, no third-party conversion API, and no document is ever used for model
training.

```
 PDF ─┐                                     ┌─ Word (DOCX)     ┌─ PDF (tools)
 Word ├─► upload ─► isolated worker ─►───────┼─ JPEG / PNG      ├─ XLSX / CSV
 Image┤   (checks)   (own process)           ├─ Text / HTML     ├─ ZIP batches
 Excel┘                                     └─ Searchable PDF  └─ Images
```

## What it does

**PDF (19 tools)** — PDF → Word, JPEG, PNG, text, Excel, searchable PDF, single
page PDFs; extract images; merge, split, extract, delete, reorder, rotate,
compress, watermark, page numbers, protect (AES-256), unlock.

**Word (5 tools)** — Word → PDF, JPEG, PNG, text, HTML. Legacy `.doc` is
supported through LibreOffice when it is installed.

**Images (7 tools)** — images → PDF (multi-image, page size, orientation,
margins), convert between JPEG/PNG/WebP/HEIC/GIF/BMP/TIFF, resize, compress,
rotate, image → text (OCR), image → Word.

**Other formats (6 tools)** — Excel → PDF, Excel → CSV, CSV → Excel,
PowerPoint → PDF (LibreOffice), text/Markdown → PDF, HTML → PDF.

The catalog is generated from the server's registry, so the interface can only
offer conversions the running server actually supports. A tool whose engine is
missing (for example PowerPoint without LibreOffice) is shown as unavailable
with the reason instead of failing at upload time.

## Quick start (Docker)

```bash
cd docupro
cp .env.example .env
docker compose up -d --build
# open http://localhost:8000
```

## Quick start (from source)

Requirements: Python 3.11+, Node 20+, and optionally Tesseract (OCR) and
LibreOffice (PowerPoint, legacy `.doc`, high-fidelity Word rendering).

```bash
cd docupro
python3 -m venv .venv && . .venv/bin/activate
pip install -r services/api/requirements-dev.txt
cd apps/web && npm ci && npm run build && cd ../..
DOCUPRO_WEB_DIR=$PWD/apps/web/dist \
  .venv/bin/python -m uvicorn docupro_api.main:app --app-dir services/api --port 8000
```

For development with hot reload, run `make api` and `make web` in two terminals
(the Vite server proxies `/api` to port 8000).

## Verification status

| Area | Status |
| --- | --- |
| Backend tests | 100 passed (`pytest`), 77% statement coverage |
| Lint / formatting | `ruff check` and `ruff format --check` clean |
| Conversion matrix | 36 of 37 verified end to end; `powerpoint-to-pdf` requires LibreOffice, which the build sandbox does not have |
| Web client | TypeScript clean; production build 89.4 kB gzipped JS + 8.3 kB CSS; jsdom smoke test and a full upload → convert → download flow pass against the live API |
| Windows / Android binaries | Shell complete and buildable through `ci/workflows/release.yml`; not built in this sandbox (no Rust/Java/Windows toolchain) |
| CI | Workflows are versioned in `ci/workflows`; the GitHub App token used here cannot push `.github/workflows` (see `ci/README.md`) |

Details and evidence: [`docs/DELIVERY-REPORT.md`](docs/DELIVERY-REPORT.md).

## Documentation

| Document | Contents |
| --- | --- |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Processes, job lifecycle, engines, storage |
| [API.md](docs/API.md) | Every endpoint, option and error code |
| [SECURITY.md](docs/SECURITY.md) | Threat model and hardening, with tests |
| [PRIVACY.md](docs/PRIVACY.md) | What is stored, for how long, and where |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Docker, Render, Fly.io, systemd + Caddy |
| [BUILD-WINDOWS.md](docs/BUILD-WINDOWS.md) | Installer and portable build |
| [BUILD-ANDROID.md](docs/BUILD-ANDROID.md) | APK/AAB build and signing |
| [TESTING.md](docs/TESTING.md) | How to reproduce every test |
| [PERFORMANCE.md](docs/PERFORMANCE.md) | Measured timings and throughput |
| [LIMITATIONS.md](docs/LIMITATIONS.md) | Honest list of what does not work perfectly |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common failures and fixes |

## Repository layout

```
docupro/
├── services/api/          FastAPI service, engines, worker, tests
├── apps/web/              React + TypeScript + Vite interface
├── apps/desktop/          Tauri v2 shell (Windows + Android), native dialogs
├── packages/shared/       Catalog contract shared by every client
├── ci/workflows/          GitHub Actions pipelines (ready to activate)
├── deploy/                systemd unit, Caddyfile
├── docs/                  Documentation and measured results
├── scripts/               Verification, benchmark, catalog and deploy helpers
└── tests/corpus/          Fixture generator (generated files are not committed)
```

## License

MIT — see [LICENSE](LICENSE).
