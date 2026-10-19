# Testing

Everything below can be reproduced from a clean checkout. Commands assume you
are in the `docupro/` directory.

## 1. Environment

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r services/api/requirements-dev.txt
cd apps/web && npm ci && cd ../..
```

Optional but used by several tests:

```bash
sudo apt-get install -y tesseract-ocr tesseract-ocr-fra libreoffice-writer libreoffice-impress
```

## 2. Fixtures

The corpus is generated, never committed (15 MB of binary fixtures would
bloat the repository):

```bash
python tests/corpus/make_corpus.py tests/corpus/generated
```

It produces 21 files: a 3-page bilingual PDF, a text-free scan, an encrypted
PDF (password `motdepasse`), an A4 DOCX with a table, image and page breaks, a
short DOCX, JPEG/PNG/WebP/HEIC images, an OCR sample, XLSX/CSV/TXT/HTML, plus
deliberately hostile inputs (empty file, truncated PDF, a `.pdf` that is really
an executable, an oversized image).

## 3. Unit and API tests

```bash
cd services/api
pytest -q
pytest -q --cov=docupro_api --cov-report=term-missing
```

What is covered (94 tests):

| File | Focus |
| --- | --- |
| `tests/test_security.py` | filename sanitiser (traversal, control characters, Unicode), signature detection, content-disposition, rate limiter |
| `tests/test_engines.py` | page-range parsing, ligature normalisation, image handling, DOCX renderer, PDF validation, encryption, OCR fallbacks |
| `tests/test_api.py` | catalog shape, security headers, full job lifecycle over HTTP, token enforcement, spoofed and corrupted uploads, wrong passwords, ordering, cancellation, deletion, expiry sweep, rate limiting, four concurrent jobs |

Tests that need an engine absent on the machine are skipped with a reason, not
silently passed.

## 4. Conversion matrix

```bash
python scripts/verify_engines.py tests/corpus/generated
```

This runs **every registered tool** in-process, validates the produced bytes
(PDF structure, DOCX openability, image decodability, non-empty output) and
prints a table. `VERBOSE=1` shows tracebacks. Exit code is non-zero if any
conversion fails.

Expected on a machine with Tesseract and LibreOffice: 37/37 pass. In this
sandbox (no LibreOffice): 36 pass, 1 skipped (`powerpoint-to-pdf`).

## 5. Web client

```bash
cd apps/web
npx tsc --noEmit          # strict type check
npm run build             # production bundle
```

Interface tests run without a browser, in jsdom, against a live server:

```bash
# terminal 1 — production server with the built client
cd docupro
DOCUPRO_WEB_DIR=$PWD/apps/web/dist DOCUPRO_DATA_DIR=/tmp/docupro-test \
  .venv/bin/python -m uvicorn docupro_api.main:app --app-dir services/api --port 8000

# terminal 2 — smoke and full flow
cd docupro/apps/web
npx esbuild src/smoke-entry.tsx --bundle --outfile=/tmp/docupro-smoke.cjs \
  --platform=node --format=cjs --alias:@=./src --jsx=automatic --define:import.meta.env='{}'
npx esbuild src/flow-entry.tsx --bundle --outfile=/tmp/docupro-flow.cjs \
  --platform=node --format=cjs --alias:@=./src --jsx=automatic --define:import.meta.env='{}'
node scripts-dom-smoke.mjs
DOCUPRO_CORPUS=$PWD/../../tests/corpus/generated node scripts/ui-flow.mjs
```

* `scripts-dom-smoke.mjs` renders the real app and asserts the hero, the tool
  grid, navigation to a tool page, the generated option form, the tools page
  and the privacy page.
* `scripts/ui-flow.mjs` attaches a real PDF to the file input, clicks
  **Convert now**, waits for the worker, checks the artifact and the recorded
  history, then repeats the flow with a corrupted PDF and asserts that an error
  is shown and no download is offered.

## 6. Deployment smoke test

```bash
python scripts/smoke_deploy.py http://localhost:8000
python scripts/smoke_deploy.py https://your-deployment.example.com
```

Checks health, headers, catalog, capabilities, the web client, a real
PDF → DOCX conversion, the download token requirement, the absence of caching
on downloads and immediate deletion. Exit code 1 on any failure, so it can gate
a deployment.

## 7. Performance

```bash
python scripts/benchmark.py tests/corpus/generated
```

Writes `docs/performance-results.json`. See `PERFORMANCE.md` for the recorded
run and its environment.

## 8. What the pipelines add

`ci/workflows/ci.yml` (activate with `scripts/install_workflows.sh`) repeats all
of the above on a clean Ubuntu runner with Tesseract and LibreOffice installed,
then builds the container, runs it, converts a document inside it and checks the
downloaded bytes. It also verifies that `packages/shared/catalog.json` matches
the registry.

## 9. Manual checklist for a release

- [ ] `pytest` green, `ruff` clean
- [ ] `verify_engines.py` 37/37 (or documented exception)
- [ ] `tsc --noEmit` and `npm run build` clean
- [ ] `smoke_deploy.py` green against the target deployment
- [ ] Upload a 20 MB PDF and a HEIC photo from a phone
- [ ] Download a result, then confirm the files disappear from disk
- [ ] Restart the service; confirm orphaned job directories are gone
