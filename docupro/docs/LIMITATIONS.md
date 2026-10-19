# Limitations

DOCUPRO prefers an honest limitation over a silently wrong result. Every tool
shows its limits in the interface, and the server refuses inputs it cannot
handle instead of producing a broken file.

## By tool

### PDF → Word
* Best for text-based PDFs with simple-to-moderate layout. Multi-column academic
  papers, magazines and complex tables are approximated, not reproduced.
* Scanned PDFs need OCR: use **Conversion mode → OCR** (automatic mode switches
  when a PDF has almost no text layer). OCR output has no original formatting.
* Fonts are substituted when the original is embedded and not extractable.
* Presentation ligatures (`ﬁ`, `ﬀ`) written by some PDF generators are
  normalised to plain letters so the Word file stays searchable.

### Word → PDF
* With LibreOffice installed, rendering is faithful (pagination, fields,
  headers, footers, numbering).
* Without LibreOffice, the built-in renderer preserves headings, lists, tables,
  images, page breaks, page size, margins, headers, footers and page numbers,
  but exact Word pagination can differ and advanced constructs (text boxes,
  floating shapes, content controls, SmartArt, equations) are simplified.
* Legacy `.doc` requires LibreOffice; the tool reports this instead of failing
  mid-conversion.

### PDF → images
* Maximum 600 dpi, and the pixel budget (80 MP per page) is enforced — a huge
  page at 600 dpi is refused with a clear message.
* Outputs are flattened rasters: text is no longer selectable.

### Searchable PDF (OCR)
* 12 language codes are offered; accuracy depends on scan quality, skew and
  language model installed.
* The invisible text layer is generated from OCR boxes; complex layouts may have
  slightly offset selectable text.
* Training is never performed on user documents.

### Compress PDF
* Downsampling only affects images. A PDF that is already optimised (text-only,
  or images below the DPI threshold) will barely shrink; the tool reports the
  actual saving and never inflates the file deliberately.
* Fonts are subset only when LibreOffice is not required for the operation.

### PDF → Excel
* Tables are detected geometrically. Borderless tables, nested tables and merged
  cells can be merged or split incorrectly.
* The extractor refuses PDFs with no detectable table rather than returning an
  empty sheet (`no_tables`).
* Each detected table becomes a sheet; very large tables are capped
  (`too_many_rows`).

### PowerPoint → PDF
* Requires LibreOffice on the server. Without it the tool is listed as
  unavailable with the reason, so no user wastes a 40 MB upload.

### Images
* HEIC/HEIF requires `pillow-heif` (installed in the image); animated GIFs are
  converted from their first frame.
* Rotating by arbitrary angles enlarges the canvas; only 90° steps are exact.
* Converting to JPEG flattens transparency onto white.

### Text / HTML → PDF
* HTML is sanitised: scripts, iframes, forms, remote stylesheets and remote
  images are removed. Local CSS in the document is partially supported (fonts,
  sizes, colours, basic layout); CSS grid/flex layouts are simplified.
* No JavaScript is executed; a page that renders only through script produces
  just its static text.

## Platform-level

* **Single instance.** Job state is in memory; run one process per deployment
  and scale with `DOCUPRO_MAX_CONCURRENCY`.
* **Retention.** Uploaded files are deleted immediately after conversion; the
  *converted* file is deleted after 30 minutes (or ~2 minutes after download).
  There is no long-term storage, so a download link is not permanent.
* **Rate limiting** is per client address. Behind a proxy, set
  `DOCUPRO_TRUST_PROXY=1` and make sure `X-Forwarded-For` is set by that proxy.
* **Offline.** The interface is installable and its shell works offline, but
  conversions always need the server.
* **Localisation.** The interface ships in English; tool IDs, options and error
  messages are stable English strings. French UI localisation is not included.
* **Accessibility.** Keyboard navigation, focus rings, ARIA live regions and
  reduced-motion support are implemented; a formal WCAG audit has not been
  performed.
* **Native builds** are produced by the release workflow on Windows and Linux
  runners. This repository's sandbox has no Rust/Java toolchain, so no binaries
  are committed or attached by the sandbox itself.

## Deliberately not included

* No AI "reconstruction" of layouts, no generative summarisation, no automatic
  document chat. Such features would either be misleading or require sending
  documents to a third party.
* No account system, cloud storage or sharing links with expiry by email.
* No conversion via public third-party APIs.
