"""Engine-level regression tests over the generated corpus."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pymupdf
import pytest

from docupro_api.engines.common import parse_page_selection
from docupro_api.engines.models import ConversionContext, SourceFile
from docupro_api.engines.registry import REGISTRY, availability, validate_options
from docupro_api.errors import ValidationError
from docupro_api.security import assert_upload_matches, sanitize_filename


def run_tool(tool: str, files: list[Path], settings, options: dict | None = None, tmp: Path | None = None):
    spec = REGISTRY[tool]
    workdir = (tmp or Path("/tmp")) / "work"
    outdir = (tmp or Path("/tmp")) / "out"
    workdir.mkdir(parents=True, exist_ok=True)
    outdir.mkdir(parents=True, exist_ok=True)
    sources = []
    for index, path in enumerate(files):
        safe = sanitize_filename(path.name)
        kind = assert_upload_matches(path, safe, spec.input.extensions, settings)
        pages = None
        if kind == "pdf":
            with pymupdf.open(path) as doc:
                pages = doc.page_count
        sources.append(
            SourceFile(
                path=path,
                original_name=path.name,
                safe_name=safe,
                kind=kind,
                size=path.stat().st_size,
                pages=pages,
                order=index,
            )
        )
    ctx = ConversionContext(
        files=sources,
        options=validate_options(spec, options or {}),
        workdir=workdir,
        outdir=outdir,
        settings=settings,
        progress=lambda f, m: None,
        is_cancelled=lambda: False,
    )
    return spec.run(ctx)


@pytest.mark.parametrize(
    "tool,fixture,options",
    [
        ("pdf-to-text", "report-fr.pdf", {}),
        ("pdf-to-word", "report-fr.pdf", {}),
        ("pdf-to-word", "scan-fr.pdf", {"mode": "ocr"}),
        ("pdf-to-jpeg", "report-fr.pdf", {"pages": "1", "dpi": 100}),
        ("pdf-to-png", "report-fr.pdf", {"pages": "1-2", "dpi": 100}),
        ("pdf-to-searchable", "scan-fr.pdf", {"dpi": 180}),
        ("pdf-extract-images", "report-fr.pdf", {}),
        ("pdf-to-single-pages", "report-fr.pdf", {}),
        ("compress-pdf", "report-fr.pdf", {}),
        ("rotate-pdf", "report-fr.pdf", {"angle": "180"}),
        ("extract-pages", "report-fr.pdf", {"pages": "1,3"}),
        ("delete-pages", "report-fr.pdf", {"pages": "1"}),
        ("reorder-pages", "report-fr.pdf", {"pages": "3,2,1"}),
        ("page-numbers", "report-fr.pdf", {"style": "n-of-total"}),
        ("watermark-pdf", "report-fr.pdf", {"text": "DRAFT"}),
        ("pdf-to-excel", "report-fr.pdf", {}),
        ("word-to-pdf", "report.docx", {}),
        ("word-to-text", "report.docx", {}),
        ("word-to-html", "report.docx", {}),
        ("word-to-jpeg", "short.docx", {"dpi": 90}),
        ("image-to-pdf", "photo.jpg", {}),
        ("image-to-text", "ocr-sample.png", {}),
        ("image-to-word", "ocr-sample.png", {}),
        ("image-convert", "logo-alpha.png", {"target_format": "jpeg"}),
        ("image-resize", "photo.jpg", {"mode": "max_edge", "width": 200}),
        ("image-compress", "photo.jpg", {}),
        ("image-rotate", "photo.jpg", {}),
        ("csv-to-excel", "data.csv", {}),
        ("excel-to-csv", "workbook.xlsx", {}),
        ("excel-to-pdf", "workbook.xlsx", {}),
        ("text-to-pdf", "plain.txt", {}),
        ("html-to-pdf", "page.html", {}),
    ],
)
def test_single_file_conversions(tool, fixture, options, corpus, settings, tmp_path):
    spec = REGISTRY[tool]
    available, reason = availability(spec)
    if not available:
        pytest.skip(reason or "engine unavailable")
    artifacts = run_tool(tool, [corpus / fixture], settings, options, tmp_path)
    assert artifacts, "engine produced no artifacts"
    for artifact in artifacts:
        assert artifact.path.exists()
        assert artifact.path.stat().st_size > 0
        assert artifact.filename
    primary = artifacts[0]
    if primary.media_type == "application/pdf":
        with pymupdf.open(primary.path) as doc:
            if doc.needs_pass:
                assert doc.authenticate(options.get("password", ""))
            else:
                assert doc.page_count >= 1
                doc.load_page(0).get_text("text")
    elif primary.filename.endswith(".docx"):
        import docx

        assert docx.Document(str(primary.path)).paragraphs
    elif primary.filename.endswith(".zip"):
        with zipfile.ZipFile(primary.path) as zf:
            assert zf.namelist()
            assert zf.testzip() is None


def test_merge_and_protect(corpus, settings, tmp_path):
    artifacts = run_tool("merge-pdf", [corpus / "report-fr.pdf", corpus / "scan-fr.pdf"], settings, {}, tmp_path)
    with pymupdf.open(artifacts[0].path) as doc:
        assert doc.page_count == 4

    protected = run_tool("protect-pdf", [corpus / "report-fr.pdf"], settings, {"password": "s3cret!"}, tmp_path)
    with pymupdf.open(protected[0].path) as doc:
        assert doc.needs_pass
        assert doc.authenticate("s3cret!")
        assert doc.page_count == 3
    # Unlocking requires the password
    with pytest.raises(ValidationError):
        run_tool("unlock-pdf", [corpus / "protected.pdf"], settings, {"password": "wrong"}, tmp_path)
    unlocked = run_tool("unlock-pdf", [corpus / "protected.pdf"], settings, {"password": "motdepasse"}, tmp_path)
    with pymupdf.open(unlocked[0].path) as doc:
        assert not doc.needs_pass


def test_multi_image_pdf_ordering(corpus, settings, tmp_path):
    artifacts = run_tool(
        "image-to-pdf",
        [corpus / "photo.jpg", corpus / "logo-alpha.png"],
        settings,
        {"order": "2,1", "page_size": "fit"},
        tmp_path,
    )
    with pymupdf.open(artifacts[0].path) as doc:
        assert doc.page_count == 2


def test_invalid_inputs_are_rejected(corpus, settings, tmp_path):
    text_only = tmp_path / "text-only.pdf"
    with pymupdf.open() as plain:
        plain.new_page().insert_text((72, 72), "No images here")
        plain.save(text_only)
    with pytest.raises(Exception):
        run_tool("pdf-to-text", [corpus / "corrupted.pdf"], settings, {}, tmp_path)
    with pytest.raises(Exception):
        run_tool("pdf-to-text", [corpus / "protected.pdf"], settings, {}, tmp_path)
    with pytest.raises(ValidationError):
        run_tool("pdf-to-text", [corpus / "report-fr.pdf"], settings, {"pages": "99"}, tmp_path)
    with pytest.raises(Exception):
        run_tool("pdf-extract-images", [text_only], settings, {}, tmp_path)


def test_watermark_and_numbering_keep_pages(corpus, settings, tmp_path):
    watermarked = run_tool("watermark-pdf", [corpus / "report-fr.pdf"], settings, {"text": "CONFIDENTIEL"}, tmp_path)
    with pymupdf.open(watermarked[0].path) as doc:
        assert doc.page_count == 3
        assert "CONFIDENTIEL" in doc[0].get_text()
    numbered = run_tool("page-numbers", [corpus / "report-fr.pdf"], settings, {"style": "page-n"}, tmp_path)
    with pymupdf.open(numbered[0].path) as doc:
        assert "Page 1 of 3" in doc[0].get_text()


def test_searchable_pdf_has_text_layer(corpus, settings, tmp_path):
    artifacts = run_tool("pdf-to-searchable", [corpus / "scan-fr.pdf"], settings, {"dpi": 200}, tmp_path)
    with pymupdf.open(artifacts[0].path) as doc:
        text = doc[0].get_text()
    assert any(word in text for word in ("Facture", "Total", "Client")), text[:200]


def test_word_to_word_roundtrip_contains_text(corpus, settings, tmp_path):
    artifacts = run_tool("pdf-to-word", [corpus / "report-fr.pdf"], settings, {}, tmp_path)
    import docx

    document = docx.Document(str(artifacts[0].path))
    text = "\n".join(p.text for p in document.paragraphs)
    assert "DOCUPRO" in text or "Rapport" in text
    assert document.tables, "the ruled table should survive conversion"


@pytest.mark.parametrize(
    "spec,count,expected",
    [
        ("", 5, [0, 1, 2, 3, 4]),
        ("all", 3, [0, 1, 2]),
        ("1", 3, [0]),
        ("2-3", 4, [1, 2]),
        ("3,1", 3, [2, 0]),
        ("1-3,5", 5, [0, 1, 2, 4]),
        ("7-", 9, [6, 7, 8]),
        ("2,2,2", 3, [1]),
    ],
)
def test_page_selection_parsing(spec, count, expected):
    assert parse_page_selection(spec, count) == expected


@pytest.mark.parametrize("spec", ["0", "4-2", "abc", "1-9x", "9"])
def test_page_selection_rejects_invalid(spec):
    with pytest.raises(ValidationError):
        parse_page_selection(spec, 3)


def test_multi_page_zip_has_expected_pages(corpus, settings, tmp_path):
    artifacts = run_tool("pdf-to-png", [corpus / "report-fr.pdf"], settings, {"pages": "1-3", "dpi": 80}, tmp_path)
    with zipfile.ZipFile(artifacts[0].path) as zf:
        assert len([n for n in zf.namelist() if n.endswith(".png")]) == 3
