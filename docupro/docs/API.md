# API reference

Base URL: the origin that serves the web client (`https://your-host`). All
paths are prefixed with `/api`. Responses are JSON unless stated otherwise.

* No authentication is required. A job ID is a 128-bit random capability, and
  downloads additionally require a per-job token.
* Every `/api/*` response carries `Cache-Control: no-store`.
* Errors use one shape:

```json
{ "error": { "code": "invalid_pages", "message": "Page 7 does not exist in this 3-page PDF.", "details": {} } }
```

* Rate limiting: 40 requests/minute with a burst of 20 per client address
  (`DOCUPRO_RATE_LIMIT`, `DOCUPRO_RATE_BURST`). Exceeding it returns **429** with
  `Retry-After`. The catalog, capabilities and health routes are never limited.

## GET /api/health

```json
{ "status": "ok", "version": "1.0.0" }
```

## GET /api/ready

```json
{ "status": "ready", "checks": { "storage": true, "queue": true } }
```

Returns `"degraded"` when the data directory is unavailable or the queue is
full. Neither endpoint touches user data.

## GET /api/capabilities

```json
{
  "version": "1.0.0",
  "engines": {
    "pdf": "MuPDF",
    "wordLayout": "pdf2docx",
    "docxRender": "html-fallback",
    "libreoffice": false,
    "ocr": "rapidocr",
    "ocrLanguages": [ { "code": "eng", "label": "English" } ],
    "images": "Pillow + pillow-heif",
    "spreadsheets": "openpyxl"
  },
  "limits": {
    "maxUploadBytes": 52428800,
    "maxJobBytes": 209715200,
    "maxFilesPerJob": 20,
    "maxPages": 500,
    "maxPixels": 80000000,
    "retentionMinutes": 30,
    "conversionTimeoutSeconds": 240,
    "maxConcurrentJobs": 2
  },
  "queue": { "jobs": { "queued": 0, "running": 0, "succeeded": 3 }, "retained": 4 },
  "privacy": { "retentionMinutes": 30, "deleteAfterDownloadSeconds": 120 }
}
```

## GET /api/tools

Returns the catalog. Each tool includes its option schema so clients can render
forms without hard-coded knowledge:

```json
{
  "categories": [ { "id": "pdf", "label": "PDF tools", "description": "Convert, edit and secure PDF documents" } ],
  "tools": [
    {
      "id": "pdf-to-word",
      "title": "PDF to Word",
      "subtitle": "Editable DOCX with real paragraphs and tables",
      "description": "Converts text-based PDFs into an editable Word document…",
      "category": "pdf",
      "input": { "extensions": ["pdf"], "label": "PDF files", "mediaTypes": ["application/pdf"], "maxFiles": 1, "allowsBatch": false },
      "outputKind": "docx",
      "outputLabel": "Word document",
      "outputExtension": "docx",
      "engine": "pdf2docx",
      "minFiles": 1,
      "maxFiles": 1,
      "batch": false,
      "zipMultiple": false,
      "options": [
        {
          "key": "mode",
          "label": "Conversion mode",
          "type": "select",
          "default": "auto",
          "choices": [ { "value": "auto", "label": "Automatic" } ],
          "help": "Automatic uses OCR when the PDF has no text layer.",
          "advanced": false
        }
      ],
      "limitations": ["Scanned pages are reconstructed with OCR…"],
      "available": true,
      "unavailableReason": null,
      "featured": true,
      "estimatedSeconds": 20
    }
  ]
}
```

Option types: `select`, `number`, `boolean`, `text`, `password`, `pages`.
`minimum`, `maximum`, `step`, `placeholder`, `required` and `advanced` are
advisory hints enforced again on the server.

## POST /api/jobs

`multipart/form-data`:

| Field | Required | Meaning |
| --- | --- | --- |
| `tool` | yes | Tool ID from `/api/tools`. |
| `files` | yes | One or more files. Repeat the field for each file. |
| `options` | no | JSON object. Unknown keys are rejected. |
| `order` | no | 1-based file order, e.g. `3,1,2` (useful for merge and image → PDF). |

Limits: 50 MB per file, 200 MB per job, 20 files, 500 PDF pages, 80 megapixels
per image, all configurable (see `.env.example`).

Response **202** with the job object:

```json
{
  "id": "8f14e45fceea167a5a36dedd4bea2543",
  "tool": "pdf-to-word",
  "status": "queued",
  "progress": 0.02,
  "message": "Waiting for a worker",
  "createdAt": 1760000000.12,
  "expiresAt": 1760002100.12,
  "inputs": [ { "name": "report.pdf", "size": 348122, "pages": 12, "kind": "pdf" } ],
  "artifacts": [],
  "error": null,
  "meta": {},
  "warnings": []
}
```

## GET /api/jobs/{id}

Same shape, with live progress. Statuses: `queued`, `running`, `succeeded`,
`failed`, `cancelled`, `expired`.

When the job succeeds:

```json
{
  "status": "succeeded",
  "progress": 1.0,
  "message": "Ready to download",
  "expiresAt": 1760002100.12,
  "expiresInSeconds": 1795,
  "artifacts": [
    {
      "id": "a1",
      "name": "report.docx",
      "mediaType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "size": 42073,
      "meta": { "pages": 3, "method": "layout", "blocks": 20 },
      "primary": true,
      "url": "/api/jobs/8f14…/download/a1?token=…"
    }
  ],
  "meta": { "outputBytes": 42073, "files": 1, "durationSeconds": 0.63 }
}
```

Progress is monotonic and reaches `1.0` only after the artifact passed the
final integrity check.

## POST /api/jobs/{id}/cancel

Stops the worker process and deletes the job directory. Idempotent. Returns the
job with `status: "cancelled"`.

## DELETE /api/jobs/{id}

Deletes the job and every file immediately, without waiting for retention.
Returns **204**.

## GET /api/jobs/{id}/download/{artifact}

Requires `?token=` exactly as returned in `artifacts[].url`. Missing or wrong
tokens return **404** (deliberately indistinguishable from an unknown job), so a
leaked job ID alone cannot retrieve a document.

Headers: `Content-Disposition: attachment; filename="…"; filename*=UTF-8''…`,
`Cache-Control: no-store, private`, `X-Content-Type-Options: nosniff`.

## GET /api/jobs

Aggregate counters only — never filenames:

```json
{ "jobs": { "queued": 0, "running": 1, "succeeded": 12, "failed": 1, "cancelled": 0, "expired": 30 },
  "retained": 44, "concurrency": 2, "maxQueue": 40 }
```

## Error codes

| HTTP | Codes |
| --- | --- |
| 400 | `unknown_tool`, `tool_unavailable`, `invalid_options`, `missing_option`, `invalid_option`, `invalid_pages`, `invalid_password`, `invalid_order`, `invalid_language`, `no_files`, `too_few_files`, `too_many_files`, `too_many_pages`, `too_many_rows`, `invalid_request`, `upload_failed`, `invalid_file`, `invalid_image`, `image_too_large`, `password_required`, `not_encrypted`, `already_searchable`, `no_tables`, `no_text` |
| 404 | `job_not_found`, `artifact_not_found`, `artifacts_gone`, `artifacts_expired`, `invalid_token` |
| 413 | `file_too_large`, `job_too_large`, `too_large` |
| 415 | `unsupported_input`, `unsupported_legacy` |
| 422 | `conversion_failed`, `ocr_failed`, `ocr_embed_failed` |
| 429 | `rate_limited` |
| 503 | `queue_full`, `ocr_unavailable`, `libreoffice_unavailable` |

Messages are written for end users, not developers, and never include stack
traces, paths or library internals.

## Integration example

```bash
# 1. start a conversion
curl -sS -X POST http://localhost:8000/api/jobs \
  -F tool=pdf-to-word -F 'options={"mode":"auto"}' \
  -F 'files=@report.pdf;type=application/pdf'

# 2. poll
curl -sS http://localhost:8000/api/jobs/<id>

# 3. download (URL comes from artifacts[0].url)
curl -fL -o report.docx 'http://localhost:8000/api/jobs/<id>/download/a1?token=<token>'
```

`scripts/smoke_deploy.py` implements exactly this flow and is used to verify a
deployed instance.
