# Performance

Measured with `scripts/benchmark.py`. Raw data: [`performance-results.json`](performance-results.json).

## Environment

| Property | Value |
| --- | --- |
| Host | Linux 6.1, x86_64, 2 vCPU, 3.9 GB RAM (container) |
| Python | 3.11.2 |
| PDF engine | PyMuPDF 1.28.2 |
| OCR | RapidOCR (ONNX) — Tesseract was not installed on this host |
| Fixtures | generated corpus (`tests/corpus/make_corpus.py`) + generated 50-page PDF and 12 MP JPEG |

These are modest numbers on a small shared VM; a 4–8 vCPU production host with
Tesseract will be faster on OCR and can run more conversions in parallel.

## Conversion timings

| Tool | Input | Median | Worst | Output |
| --- | --- | ---: | ---: | ---: |
| PDF → text | 3-page PDF | 0.011 s | 0.014 s | 2 KB |
| PDF → Word | 3-page PDF | 0.34 s | 0.46 s | 41 KB |
| PDF → JPEG (150 dpi) | 3-page PDF | 0.27 s | 0.28 s | 176 KB |
| PDF → searchable PDF | 1-page scan | 2.14 s | 2.85 s | 427 KB |
| Compress PDF | 3-page PDF | 0.015 s | 0.016 s | 20 KB |
| Merge PDFs | 3 × 3 pages | 0.016 s | 0.02 s | 15 KB |
| Images → PDF | 4 images | 0.023 s | 0.03 s | 38 KB |
| Resize image | 1200×900 JPEG | 0.012 s | 0.013 s | 16 KB |
| Word → PDF | A4 DOCX, 3 pages | 0.11 s | 0.12 s | 475 KB |
| PDF → Excel | 3-page PDF with tables | 0.046 s | 0.10 s | 6 KB |
| PDF → text | **50 pages** | 0.14 s | 0.14 s | 33 KB |
| PDF → Word | **50 pages** | 5.41 s | 5.42 s | 54 KB |
| PDF → JPEG (150 dpi) | **50 pages** | 4.31 s | 4.38 s | 2.9 MB |
| Compress PDF | **50 pages** | 0.17 s | 0.17 s | 22 KB |
| 12 MP JPEG → PDF | 3000×2000 | 0.042 s | 0.044 s | 392 KB |

Throughput on one worker: **≈352 pages/s** for text extraction, **≈11.6 pages/s**
for rasterisation at 150 dpi and **≈9.2 pages/s** for layout-preserving
PDF → Word (all measured on the 50-page fixture). Two workers (the default)
roughly double this for independent jobs.

## Memory

Peak resident memory of a single conversion process:

| Tool | Peak RSS |
| --- | ---: |
| Word → PDF (built-in renderer) | 80 MB |
| Images → PDF | 69 MB |
| PDF → Word (3 pages) | 120 MB |
| PDF → searchable PDF (OCR) | 648 MB |
| Full benchmark process (every engine loaded, incl. OCR model) | 1.09 GB |

Practical sizing: allow **1 GB per concurrent OCR job** and **512 MB per
concurrent non-OCR job**. The reference container uses `mem_limit: 2g` with
`DOCUPRO_MAX_CONCURRENCY=2`.

## Upload and download

* Uploads are streamed to disk in 256 KB chunks with no in-memory buffering, so
  a 50 MB upload does not add 50 MB to RSS.
* Downloads are served with `FileResponse` (sendfile where available), so a
  3 MB artifact does not pass through Python memory.
* The API adds roughly 20–40 ms of overhead per request on this host (polling
  every 0.9 s is negligible compared with conversion time).

## Where the time goes

* **PDF → Word**: pdf2docx layout analysis dominates (~80%).
* **PDF → images**: rasterisation at 150 dpi is linear in page count; PNG is
  ~2× slower than JPEG at the same DPI.
* **OCR**: ~1.4–2.1 s per A4 page at 200 dpi with RapidOCR; Tesseract is
  typically faster and more accurate on clean scans.
* **Word → PDF with LibreOffice**: 0.6–1.5 s of LibreOffice start-up per
  conversion, plus rendering. The built-in fallback used here is much faster but
  less faithful for complex layouts.
* **Compression** on already-optimised PDFs is fast because there are no
  oversized images to downsample; the gain is limited (see `LIMITATIONS.md`).

## Reproducing

```bash
python scripts/benchmark.py tests/corpus/generated
```

The script prints each case and rewrites `docs/performance-results.json` with
timestamps and environment information.
