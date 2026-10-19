# Troubleshooting

## The interface shows "The conversion service is unreachable"

* Check `curl https://your-host/api/health`.
* If the API works but the interface is on another origin, set
  `DOCUPRO_CORS_ORIGINS=https://your-interface.example.com` and restart.
* If the interface was built with `VITE_API_BASE`, confirm the URL has no
  trailing slash and uses HTTPS when the page is HTTPS (mixed content is blocked
  by browsers).

## "This tool is not available on this server"

The engine is missing. `GET /api/capabilities` shows `libreoffice: false` when:

* **PowerPoint → PDF** needs `libreoffice-impress`,
* **Legacy `.doc`** needs `libreoffice-writer`,
* **Excel → PDF** needs `libreoffice-calc`.

Install LibreOffice in the image (the default `Dockerfile` does), or use the
built-in alternatives (Word → PDF works without it).

## OCR says no engine is available

Install Tesseract (`apt-get install tesseract-ocr tesseract-ocr-fra`) or install
the pip fallback:

```bash
pip install -r services/api/requirements-ocr.txt
```

`GET /api/capabilities` → `engines.ocr` reports `tesseract`, `rapidocr` or
`null`.

## "Too many requests"

The token bucket (40 req/min, burst 20) is exhausted. Wait for the number of
seconds in `Retry-After`. If a reverse proxy does not forward the real client
address, every user shares one bucket: enable `DOCUPRO_TRUST_PROXY=1` and make
sure the proxy sets `X-Forwarded-For`.

## "The conversion queue is full"

More than `DOCUPRO_MAX_QUEUE` (40) jobs are waiting. Raise
`DOCUPRO_MAX_CONCURRENCY` if the host has CPU and memory, or raise the queue
limit, then restart.

## A large PDF fails with "too many pages"

`DOCUPRO_MAX_PAGES` defaults to 500. Raise it only together with memory: a
300-page colour PDF can need >1 GB during rasterisation.

## Conversion times out

`DOCUPRO_CONVERSION_TIMEOUT` (240 s) is the wall-clock limit. Very large OCR
jobs exceed it on small hosts. Lower the DPI, convert fewer pages, or raise the
timeout and give the container more CPU.

## Downloaded file is 0 bytes or missing

The server validates every artifact before offering it; a 0-byte file is never
announced. If a download now fails:

* the retention window may have elapsed (`expiresInSeconds` in the job JSON),
* the job may have been deleted from another tab,
* the token may be missing — the download URL must keep `?token=…`.

## Files do not disappear from disk

Check that the service can write and delete inside `DOCUPRO_DATA_DIR`. The
sweeper logs `expired and was cleaned`. A read-only volume or wrong ownership
(container user `10001`) prevents deletion.

## Docker build fails at `apt-get install libreoffice`

The Office image needs ~1.5 GB of disk during build. Build with
`--build-arg INSTALL_OFFICE=0` for a 450 MB image without Office conversions, or
free disk space.

## Windows app: SmartScreen warning

Unsigned installers always trigger it. Sign the build (see `BUILD-WINDOWS.md`)
or choose "More info → Run anyway" for a local build.

## Android app: "App not installed"

The release APK is unsigned unless a keystore is configured. Install the debug
APK, or sign the release build with your keystore.

## Service worker serves an old interface

The PWA caches the app shell. A new deployment changes the asset hashes, and the
worker fetches the new `index.html` on the next navigation. To force it: close
all tabs of the app and reopen, or clear site data. `src/main.tsx` registers the
worker only in production builds, so development is never cached.

## Reset everything

```bash
docker compose down -v      # removes the data volume
docker compose up -d --build
```

This deletes all pending conversions; configuration in `.env` is kept.
