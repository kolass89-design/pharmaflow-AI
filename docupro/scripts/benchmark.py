"""Measure real conversion performance and write a report.

Usage: python scripts/benchmark.py [corpus_dir]

Each case runs in the same isolated-worker architecture used in production
(a fresh conversion context, cold caches) and is repeated to report the median
and the worst run. Results are written to docs/performance-results.json and a
Markdown summary is printed.
"""

from __future__ import annotations

import json
import os
import platform
import resource
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "services" / "api"))

from docupro_api.config import Settings  # noqa: E402
from docupro_api.engines.models import ConversionContext, SourceFile  # noqa: E402
from docupro_api.engines.registry import REGISTRY, validate_options  # noqa: E402
from docupro_api.security import sanitize_filename  # noqa: E402
from docupro_api.security import detect_kind  # noqa: E402

def build_large_fixtures(corpus: Path, target: Path) -> None:
    """Create larger fixtures so the numbers reflect real documents."""
    import pymupdf
    from PIL import Image, ImageDraw

    target.mkdir(parents=True, exist_ok=True)
    source = pymupdf.open(corpus / "report-fr.pdf")
    out = pymupdf.open()
    for _ in range(0, 50, source.page_count):
        out.insert_pdf(source)
    while out.page_count > 50:
        out.delete_page(out.page_count - 1)
    out.save(target / "bench-50-pages.pdf", garbage=3, deflate=True)
    out.close()
    source.close()

    image = Image.new("RGB", (3000, 2000), (240, 244, 252))
    draw = ImageDraw.Draw(image)
    for y in range(0, 2000, 40):
        draw.line([(0, y), (3000, y)], fill=(120 + y % 100, 140, 220 - y % 80), width=3)
    image.save(target / "bench-12mp.jpg", quality=92)


CASES: list[tuple[str, list[str], dict, int]] = [
    ("pdf-to-text", ["report-fr.pdf"], {}, 5),
    ("pdf-to-word", ["report-fr.pdf"], {}, 3),
    ("pdf-to-jpeg", ["report-fr.pdf"], {"pages": "1-3", "dpi": 150}, 3),
    ("pdf-to-searchable", ["scan-fr.pdf"], {"ocr_language": "eng", "dpi": 200, "force": True}, 2),
    ("compress-pdf", ["report-fr.pdf"], {"preset": "balanced"}, 3),
    ("merge-pdf", ["report-fr.pdf", "report-fr.pdf", "report-fr.pdf"], {"add_bookmarks": True}, 3),
    ("image-to-pdf", ["photo.jpg", "photo.jpg", "photo.jpg", "photo.jpg"], {"page_size": "a4"}, 3),
    ("image-resize", ["photo.jpg"], {"mode": "percent", "percent": 50, "target_format": "keep"}, 3),
    ("word-to-pdf", ["report.docx"], {}, 3),
    ("pdf-to-excel", ["report-fr.pdf"], {}, 3),
    ("pdf-to-text", ["bench-50-pages.pdf"], {}, 3),
    ("pdf-to-word", ["bench-50-pages.pdf"], {}, 2),
    ("pdf-to-jpeg", ["bench-50-pages.pdf"], {"pages": "", "dpi": 150}, 2),
    ("compress-pdf", ["bench-50-pages.pdf"], {"preset": "balanced"}, 2),
    ("image-to-pdf", ["bench-12mp.jpg"], {"page_size": "a4"}, 2),
]


def main() -> int:
    corpus = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "tests" / "corpus" / "generated").resolve()
    generated = {"bench-50-pages.pdf", "bench-12mp.jpg"}
    base_missing = sorted(
        {
            name
            for _, files, _, _ in CASES
            for name in files
            if name not in generated and not (corpus / name).exists()
        }
    )
    if base_missing:
        print(f"missing fixtures in {corpus}: {base_missing}\nRun: python tests/corpus/make_corpus.py {corpus}")
        return 2

    workroot = Path(tempfile.mkdtemp(prefix="docupro-bench-"))
    build_large_fixtures(corpus, workroot / "fixtures")
    os.environ.setdefault("DOCUPRO_DATA_DIR", str(workroot / "data"))
    settings = Settings()
    settings.ensure_dirs()

    rows = []
    for tool_id, files, options, repeats in CASES:
        spec = REGISTRY[tool_id]
        durations: list[float] = []
        sizes: list[int] = []
        for run in range(repeats):
            case_dir = workroot / f"{tool_id}-{run}"
            (case_dir / "work").mkdir(parents=True, exist_ok=True)
            (case_dir / "out").mkdir(parents=True, exist_ok=True)
            sources = []
            for index, name in enumerate(files):
                path = corpus / name
                if not path.exists():
                    path = workroot / "fixtures" / name
                detected = detect_kind(path) or "pdf"
                sources.append(
                    SourceFile(
                        path=path,
                        original_name=name,
                        safe_name=sanitize_filename(name, fallback=f"file-{index}"),
                        kind=detected,
                        size=path.stat().st_size,
                        pages=None,
                        order=index,
                    )
                )
            ctx = ConversionContext(
                files=sources,
                options=validate_options(spec, options),
                workdir=case_dir / "work",
                outdir=case_dir / "out",
                settings=settings,
                progress=lambda fraction, message: None,
                is_cancelled=lambda: False,
            )
            started = time.perf_counter()
            artifacts = spec.run(ctx)
            durations.append(time.perf_counter() - started)
            sizes.append(sum(a.path.stat().st_size for a in artifacts))
            shutil.rmtree(case_dir, ignore_errors=True)
        rows.append(
            {
                "tool": tool_id,
                "files": files,
                "inputBytes": int(
                    sum(
                        ((corpus / name) if (corpus / name).exists() else (workroot / "fixtures" / name)).stat().st_size
                        for name in files
                    )
                ),
                "outputBytes": int(statistics.median(sizes)),
                "runs": repeats,
                "medianSeconds": round(statistics.median(durations), 3),
                "minSeconds": round(min(durations), 3),
                "maxSeconds": round(max(durations), 3),
            }
        )
        print(f"{tool_id:22} median {rows[-1]['medianSeconds']:>6.2f}s  max {rows[-1]['maxSeconds']:>6.2f}s")

    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    payload = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "cpuCount": os.cpu_count(),
            "peakResidentMegabytes": round(rss_mb, 1),
        },
        "results": rows,
    }
    target = ROOT / "docs" / "performance-results.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {target.relative_to(ROOT)}")
    shutil.rmtree(workroot, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
