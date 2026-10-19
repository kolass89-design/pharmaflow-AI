# Security

DOCUPRO processes untrusted files. This document describes the threat model,
the controls that are implemented, and how each control is tested.

## Threat model

| Adversary | Goal | Mitigation |
| --- | --- | --- |
| Anonymous internet user | Use the service as free compute or storage | Rate limiting, queue cap, upload/job size caps, 30-minute retention |
| Attacker uploading a malicious file | Execute code, escape the parser, exhaust memory | Signature validation, isolated worker process, CPU/file-size rlimits, wall-clock timeout, OOXML zip-bomb limits, pixel caps |
| Attacker guessing URLs | Read someone else's document | 128-bit random job IDs plus a separate download token; wrong token returns 404 |
| Attacker with a leaked job ID | Download a document | Token is required and never appears in the job list, logs or the UI history |
| User of a shared computer | See another person's documents | No accounts, no server-side history, browser history is opt-in and local |
| Network attacker | Read or modify traffic | HTTPS behind a TLS-terminating proxy; HSTS, no-store, nosniff, no-referrer headers |
| Malicious document content | Exfiltrate data through HTML/scripts | HTML is parsed with an allow-list sanitiser; scripts, iframes, objects, forms and remote URLs are dropped; no network access from renderers |

## Upload validation

1. Filenames are sanitised (`basename`, control characters removed, length
   capped, `.` runs collapsed) and never used as paths on disk. Uploads are
   stored as `input/NNN-<random>.<ext>` under a `0700` directory.
2. The declared extension is checked against the tool's accepted inputs.
3. The file signature is inspected and must match the declared kind:
   `%PDF-`, OOXML zip + `[Content_Types].xml`, JPEG/PNG/WebP/HEIF/GIF/BMP/TIFF
   magic, or decodable UTF-8 text. A `.pdf` file containing an executable is
   rejected with `415 unsupported_input`.
4. PDFs are opened before the worker starts; encrypted files are reported
   (`password_required`) and page counts are enforced.
5. Images are probed for dimensions; `Image.MAX_IMAGE_PIXELS` and an explicit
   pixel budget stop decompression bombs.
6. OOXML archives are checked for entry count and total uncompressed size, which
   blocks zip bombs before parsing.

Tests: `test_security.py` (sanitiser, signatures, content disposition,
rate limiter) and `test_api.py` (spoofed extension, executable upload, empty
file, corrupted PDF, zip bomb, traversal filename).

## Process isolation

* Each conversion runs in a **separate process** started with a fixed argument
  (`python -m docupro_api.worker <job_dir>`) and a sanitised environment. No
  user-controlled value reaches the command line or the environment.
* `RLIMIT_CPU`, `RLIMIT_FSIZE` and `RLIMIT_NOFILE` are applied in the child.
* The parent enforces the wall-clock deadline (`DOCUPRO_CONVERSION_TIMEOUT`,
  240 s), then terminates and, if needed, kills the worker.
* The worker writes into a private directory and may only report artifacts that
  exist, are non-empty and resolve inside `output/`. The parent re-validates.
* Cancellation and deletion terminate the process before removing files.

## Memory and CPU abuse

| Control | Default |
| --- | --- |
| Requests per minute / burst | 40 / 20 per client |
| Concurrent conversions | 2 |
| Queue length | 40 |
| Per-file upload | 50 MB |
| Per-job upload | 200 MB |
| Files per job | 20 |
| PDF pages | 500 |
| Image pixels | 80 MP |
| OOXML entries | 5 000 |
| OOXML uncompressed size | 300 MB |
| Conversion wall clock | 240 s |

The container additionally runs with `no-new-privileges`, all capabilities
dropped, a read-only root filesystem, a size-limited `/tmp`, a `pids` limit and
a memory limit.

## Network and HTTP hardening

* `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`,
  `Permissions-Policy` with camera/microphone/geolocation disabled,
  `Cross-Origin-Opener-Policy: same-origin`.
* API responses: `Content-Security-Policy: default-src 'none'`,
  `Cache-Control: no-store`.
* The web client is served with a CSP that allows only same-origin scripts,
  styles, fonts and images (`data:`/`blob:` for previews).
* HSTS is sent when the request arrived over HTTPS.
* CORS is closed unless `DOCUPRO_CORS_ORIGINS` is set; credentials are never
  allowed.
* Interactive API documentation is disabled unless `DOCUPRO_ENABLE_DOCS=1`.
* Uvicorn runs with `--no-server-header` in the container.
* HTML → PDF never fetches remote resources: the sanitiser removes remote
  images, stylesheets, `<base>`, `<meta http-equiv>` redirects and scripts.

## Secrets

The application needs no API keys, database credentials or signing keys to run.
Deployment secrets (Render hook, Fly token, Android keystore) exist only in
GitHub Actions secrets and are never committed, logged or printed by the
workflows. The Android release workflow signs only when the keystore secrets are
present; otherwise it produces clearly named unsigned/debug artifacts.

## Data handling

* Uploaded files are deleted when a conversion succeeds, fails or is cancelled.
* Outputs are deleted after 30 minutes, or 120 s after the last artifact has
  been downloaded. Users can delete immediately from the result screen.
* No document content, filename or hash is written to logs. Logs contain job
  IDs, tool IDs, durations and error codes.
* A sweeper removes expired jobs and directories orphaned by a restart.

## Reporting a vulnerability

Open a private security advisory on the repository or email the maintainer.
Please include the tool ID, a minimal input file and the observed behaviour. Do
not open a public issue for an unreported vulnerability.

## What is not covered

* Denial of service by an attacker who can create unlimited distinct source
  addresses (rate limiting is per client address).
* Malicious documents that exploit a vulnerability inside MuPDF, LibreOffice,
  Tesseract or Pillow itself. Keep dependencies updated; `security.yml` runs
  `pip-audit` and `npm audit` weekly.
* Confidentiality of files on the host disk if the host itself is compromised;
  use disk encryption and the provided sandboxing.
