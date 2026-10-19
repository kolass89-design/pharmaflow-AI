"""Security unit tests: validation, sanitisation, abuse protection."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from docupro_api.config import get_settings
from docupro_api.errors import UnsupportedInput, ValidationError
from docupro_api.security import (
    RateLimiter,
    assert_ooxml_safe,
    assert_upload_matches,
    content_disposition,
    detect_kind,
    sanitize_filename,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("../../etc/passwd", "_._etc_passwd"),
        ("..\\..\\windows\\system32\\cmd.exe", "_._windows_system32_cmd.exe"),
        ("normal report.pdf", "normal report.pdf"),
        ("file\x00name.pdf", "filename.pdf"),
        ("CON.txt", "_CON.txt"),
        ("", "document"),
        ("....", "document"),
        ("été 2026.pdf", "été 2026.pdf"),
    ],
)
def test_sanitize_filename(raw, expected):
    assert sanitize_filename(raw) == expected


def test_sanitize_filename_length():
    name = sanitize_filename("a" * 400 + ".pdf")
    assert len(name) <= 120
    assert name.endswith(".pdf")


def test_detect_kind(tmp_path: Path, corpus: Path):
    assert detect_kind(corpus / "report-fr.pdf") == "pdf"
    assert detect_kind(corpus / "photo.jpg") == "jpeg"
    assert detect_kind(corpus / "ocr-sample.png") == "png"
    assert detect_kind(corpus / "photo.webp") == "webp"
    assert detect_kind(corpus / "report.docx") == "docx"
    assert detect_kind(corpus / "workbook.xlsx") == "xlsx"
    assert detect_kind(corpus / "data.csv") == "text"
    assert detect_kind(corpus / "huge.exe") == "binary"
    assert detect_kind(corpus / "empty.pdf") == "empty"


def test_extension_spoofing_is_rejected(corpus: Path):
    with pytest.raises(UnsupportedInput):
        assert_upload_matches(corpus / "fake.pdf", "fake.pdf", ("pdf",), get_settings())
    with pytest.raises(UnsupportedInput):
        assert_upload_matches(corpus / "notes.pdf", "notes.pdf", ("pdf",), get_settings())


def test_executable_rejected(corpus: Path):
    with pytest.raises(UnsupportedInput):
        assert_upload_matches(corpus / "huge.exe", "huge.exe", ("pdf", "docx"), get_settings())


def test_empty_file_rejected(tmp_path: Path):
    empty = tmp_path / "empty.pdf"
    empty.write_bytes(b"")
    with pytest.raises(ValidationError):
        assert_upload_matches(empty, "empty.pdf", ("pdf",), get_settings())


def test_unexpected_extension_rejected(corpus: Path):
    with pytest.raises(UnsupportedInput):
        assert_upload_matches(corpus / "photo.jpg", "photo.jpg", ("pdf",), get_settings())


def test_pdf_and_images_accepted(corpus: Path):
    settings = get_settings()
    assert assert_upload_matches(corpus / "report-fr.pdf", "rapport.pdf", ("pdf",), settings) == "pdf"
    assert assert_upload_matches(corpus / "photo.jpg", "photo.jpg", ("jpg", "jpeg"), settings) == "jpeg"
    kind = assert_upload_matches(corpus / "report.docx", "report.docx", ("docx",), settings)
    assert kind == "docx"


def test_zip_bomb_rejected(tmp_path: Path):
    from dataclasses import replace

    tight = replace(get_settings(), max_ooxml_uncompressed=1024 * 1024)
    bomb = tmp_path / "bomb.docx"
    with zipfile.ZipFile(bomb, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("word/document.xml", "<w/>")
        payload = b"\x00" * (1024 * 1024)
        for index in range(12):
            zf.writestr(f"word/media/blob{index}.bin", payload)
    with pytest.raises(UnsupportedInput):
        assert_ooxml_safe(bomb, tight)


def test_ooxml_traversal_rejected(tmp_path: Path):
    archive = tmp_path / "trav.docx"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("../../evil.xml", "<x/>")
    with pytest.raises(UnsupportedInput):
        assert_ooxml_safe(archive, get_settings())


def test_rate_limiter_token_bucket():
    limiter = RateLimiter(60, 3)
    assert limiter.check("client-a")[0]
    assert limiter.check("client-a")[0]
    assert limiter.check("client-a")[0]
    allowed, retry = limiter.check("client-a")
    assert not allowed and retry >= 1
    assert limiter.check("client-b")[0]


def test_content_disposition_unicode():
    header = content_disposition("rapport été.pdf")
    assert header.startswith("attachment;")
    assert "filename*=UTF-8''rapport%20%C3%A9t%C3%A9.pdf" in header
    assert 'filename="rapport ete.pdf"' in header
    assert "\n" not in header
