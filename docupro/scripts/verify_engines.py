"""Run every registered conversion against the test corpus, in-process.

This is the engine-level acceptance suite used during development and by CI
(``pytest`` covers the same paths through the HTTP API). It prints a table of
results so the actual evidence can be pasted into the verification report.

Usage: python scripts/verify_engines.py [corpus_dir]
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "services" / "api"))

from docupro_api.config import Settings  # noqa: E402
from docupro_api.engines.models import ConversionContext, SourceFile  # noqa: E402
from docupro_api.engines.registry import REGISTRY, availability  # noqa: E402
from docupro_api.security import sanitize_filename  # noqa: E402
from docupro_api.uploads import IMAGE_KINDS  # noqa: E402
from docupro_api.security import assert_upload_matches  # noqa: E402
import pymupdf  # noqa: E402

CASES: dict[str, dict] = {
    "pdf-to-word": {"files": ["report-fr.pdf"]},
    "pdf-to-jpeg": {"files": ["report-fr.pdf"], "options": {"pages": "1-2", "dpi": 120}},
    "pdf-to-png": {"files": ["report-fr.pdf"], "options": {"pages": "1"}},
    "pdf-to-searchable": {"files": ["scan-fr.pdf"], "options": {"dpi": 200}},
    "pdf-to-text": {"files": ["report-fr.pdf"]},
    "pdf-extract-images": {"files": ["report-fr.pdf"]},
    "pdf-to-single-pages": {"files": ["short-scan.pdf"]},
    "merge-pdf": {"files": ["report-fr.pdf", "scan-fr.pdf"]},
    "split-pdf": {"files": ["report-fr.pdf"], "options": {"split_mode": "chunks", "chunk_size": 2}},
    "extract-pages": {"files": ["report-fr.pdf"], "options": {"pages": "1,3"}},
    "delete-pages": {"files": ["report-fr.pdf"], "options": {"pages": "2"}},
    "reorder-pages": {"files": ["report-fr.pdf"], "options": {"pages": "3,1,2"}},
    "rotate-pdf": {"files": ["report-fr.pdf"], "options": {"angle": "90"}},
    "compress-pdf": {"files": ["report-fr.pdf"], "options": {"preset": "balanced"}},
    "protect-pdf": {"files": ["report-fr.pdf"], "options": {"password": "secret123"}},
    "unlock-pdf": {"files": ["protected.pdf"], "options": {"password": "motdepasse"}},
    "page-numbers": {"files": ["report-fr.pdf"], "options": {"style": "page-n"}},
    "watermark-pdf": {"files": ["report-fr.pdf"], "options": {"text": "CONFIDENTIEL", "layout": "diagonal"}},
    "pdf-to-excel": {"files": ["report-fr.pdf"]},
    "word-to-pdf": {"files": ["report.docx"]},
    "word-to-jpeg": {"files": ["short.docx"], "options": {"dpi": 110}},
    "word-to-png": {"files": ["short.docx"], "options": {"dpi": 110}},
    "word-to-text": {"files": ["report.docx"]},
    "word-to-html": {"files": ["report.docx"]},
    "image-to-pdf": {"files": ["photo.jpg", "logo-alpha.png", "photo.webp", "photo.heic"], "options": {"page_size": "a4", "margin": 8}},
    "image-to-word": {"files": ["ocr-sample.png"]},
    "image-to-text": {"files": ["ocr-sample.png"]},
    "image-convert": {"files": ["photo.jpg", "logo-alpha.png"], "options": {"target_format": "png"}},
    "image-resize": {"files": ["photo.jpg"], "options": {"mode": "width", "width": 480}},
    "image-compress": {"files": ["photo.jpg"], "options": {"quality": 60}},
    "image-rotate": {"files": ["photo.jpg"], "options": {"angle": "90"}},
    "excel-to-pdf": {"files": ["workbook.xlsx"]},
    "powerpoint-to-pdf": {"files": [], "skip": "requires LibreOffice"},
    "csv-to-excel": {"files": ["data.csv"]},
    "excel-to-csv": {"files": ["workbook.xlsx"]},
    "text-to-pdf": {"files": ["plain.txt"]},
    "html-to-pdf": {"files": ["page.html"]},
}


def build_sources(paths: list[Path], settings: Settings) -> list[SourceFile]:
    sources = []
    for index, path in enumerate(paths):
        safe = sanitize_filename(path.name)
        kind = assert_upload_matches(path, safe, (path.suffix.lstrip("."),), settings)
        pages = None
        if kind == "pdf":
            with pymupdf.open(path) as doc:
                pages = doc.page_count
        sources.append(
            SourceFile(path=path, original_name=path.name, safe_name=safe, kind=kind, size=path.stat().st_size, pages=pages, order=index)
        )
    return sources


def main() -> int:
    corpus = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "tests" / "corpus" / "generated").resolve()
    workroot = Path(tempfile.mkdtemp(prefix="docupro-verify-"))
    os.environ.setdefault("DOCUPRO_DATA_DIR", str(workroot / "data"))
    settings = Settings()
    os.environ.setdefault("DOCUPRO_MAX_UPLOAD_MB", "80")
    settings = Settings()
    settings.ensure_dirs()

    # derive a single-page scan for split tests
    if (corpus / "scan-fr.pdf").exists() and not (corpus / "short-scan.pdf").exists():
        with pymupdf.open(corpus / "scan-fr.pdf") as doc:
            doc.select([0])
            doc.save(corpus / "short-scan.pdf")

    results = []
    failures = 0
    for tool_id, case in CASES.items():
        spec = REGISTRY[tool_id]
        available, reason = availability(spec)
        row = {"tool": tool_id, "status": "", "seconds": 0.0, "artifacts": [], "detail": ""}
        if case.get("skip"):
            row["status"] = "skipped"
            row["detail"] = case["skip"]
            results.append(row)
            continue
        if not available:
            row["status"] = "unavailable"
            row["detail"] = reason or ""
            results.append(row)
            continue
        files = [corpus / name for name in case["files"]]
        missing = [str(f) for f in files if not f.exists()]
        if missing:
            row["status"] = "error"
            row["detail"] = f"missing fixtures: {missing}"
            failures += 1
            results.append(row)
            continue
        jobdir = workroot / "jobs" / tool_id
        (jobdir / "work").mkdir(parents=True, exist_ok=True)
        (jobdir / "output").mkdir(parents=True, exist_ok=True)
        from docupro_api.engines.registry import validate_options

        options = validate_options(spec, case.get("options") or {})
        ctx = ConversionContext(
            files=build_sources(files, settings),
            options=options,
            workdir=jobdir / "work",
            outdir=jobdir / "output",
            settings=settings,
            progress=lambda f, m: None,
            is_cancelled=lambda: False,
        )
        started = time.time()
        try:
            artifacts = spec.run(ctx)
            row["seconds"] = round(time.time() - started, 2)
            for artifact in artifacts:
                size = artifact.path.stat().st_size
                if size <= 0:
                    raise AssertionError(f"empty artifact {artifact.filename}")
                row["artifacts"].append(f"{artifact.filename} ({size // 1024} KB)")
                if artifact.media_type == "application/pdf":
                    with pymupdf.open(artifact.path) as check:
                        assert check.page_count > 0
                        if not check.needs_pass:
                            check.load_page(0).get_text("text")
                        else:
                            row["detail"] = "encrypted output verified with password"
                            assert check.authenticate(case.get("options", {}).get("password", ""))
                elif artifact.filename.endswith(".docx"):
                    import docx

                    docx.Document(str(artifact.path))
                elif artifact.filename.endswith((".png", ".jpg", ".jpeg", ".webp")):
                    from PIL import Image

                    with Image.open(artifact.path) as img:
                        img.load()
            row["status"] = "pass"
            row["detail"] = (artifacts[0].meta if artifacts else "") and json.dumps(artifacts[0].meta)[:120]
        except Exception as exc:
            failures += 1
            row["status"] = "FAIL"
            row["detail"] = f"{type(exc).__name__}: {exc}"
            row["seconds"] = round(time.time() - started, 2)
            if os.environ.get("VERBOSE"):
                traceback.print_exc()
        results.append(row)

    width = max(len(r["tool"]) for r in results)
    print(f"\n{'TOOL'.ljust(width)}  STATUS     TIME   ARTIFACTS")
    print("-" * (width + 46))
    for row in results:
        print(f"{row['tool'].ljust(width)}  {row['status'].ljust(9)} {row['seconds']:>6}s  {', '.join(row['artifacts']) or row['detail']}")
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "pass")
    print(f"\n{passed}/{total} passed, {failures} failed, "
          f"{sum(1 for r in results if r['status'] == 'skipped')} skipped, "
          f"{sum(1 for r in results if r['status'] == 'unavailable')} unavailable")
    print(f"Working files: {workroot}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
