"""Output verification.

A conversion is only successful if the produced file is structurally valid.
These checks run before any download link is exposed, so a broken engine or a
silent crash can never be presented to the user as success.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pymupdf
from PIL import Image

from ..errors import ConversionFailed


def validate_pdf(path: Path, *, min_pages: int = 1) -> int:
    """Return the page count, raising if the PDF is unreadable."""
    if not path.exists() or path.stat().st_size == 0:
        raise ConversionFailed("The generated PDF is empty.")
    try:
        with pymupdf.open(path) as doc:
            pages = doc.page_count
            if pages < min_pages:
                raise ConversionFailed("The generated PDF contains no pages.")
            # Force a content parse so truncated documents fail here, not later.
            doc.load_page(0).get_text("text")
            return pages
    except ConversionFailed:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise ConversionFailed("The generated PDF could not be validated.") from exc


def validate_docx(path: Path) -> int:
    """Return the paragraph count of a generated DOCX."""
    if not path.exists() or path.stat().st_size == 0:
        raise ConversionFailed("The generated Word document is empty.")
    try:
        with zipfile.ZipFile(path) as zf:
            names = set(zf.namelist())
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                raise ConversionFailed("The generated Word document is not a valid OOXML package.")
            if zf.testzip() is not None:
                raise ConversionFailed("The generated Word document is corrupt.")
        import docx

        parsed = docx.Document(str(path))
        body_items = len(parsed.paragraphs) + len(parsed.tables)
        if body_items == 0:
            raise ConversionFailed("The generated Word document contains no content.")
        return body_items
    except ConversionFailed:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise ConversionFailed("The generated Word document could not be validated.") from exc


def validate_image(path: Path, *, expected_format: str | None = None) -> tuple[int, int]:
    """Return (width, height) after fully decoding the image."""
    if not path.exists() or path.stat().st_size == 0:
        raise ConversionFailed("The generated image is empty.")
    try:
        with Image.open(path) as img:
            img.load()
            width, height = img.size
            fmt = img.format
        if width <= 0 or height <= 0:
            raise ConversionFailed("The generated image has invalid dimensions.")
        if expected_format and fmt and fmt.upper() != expected_format.upper():
            raise ConversionFailed(f"Expected a {expected_format} image but produced {fmt}.")
        return width, height
    except ConversionFailed:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise ConversionFailed("The generated image could not be validated.") from exc


def validate_xlsx(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        raise ConversionFailed("The generated spreadsheet is empty.")
    try:
        from openpyxl import load_workbook

        wb = load_workbook(str(path), read_only=True)
        sheets = len(wb.sheetnames)
        wb.close()
        if sheets == 0:
            raise ConversionFailed("The generated spreadsheet has no worksheets.")
        return sheets
    except ConversionFailed:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise ConversionFailed("The generated spreadsheet could not be validated.") from exc


def validate_text(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        raise ConversionFailed("No text could be extracted from this document.")
    return path.stat().st_size


def validate_zip(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        raise ConversionFailed("The generated archive is empty.")
    try:
        with zipfile.ZipFile(path) as zf:
            bad = zf.testzip()
            if bad is not None:
                raise ConversionFailed("The generated archive is corrupt.")
            return len(zf.namelist())
    except ConversionFailed:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise ConversionFailed("The generated archive could not be validated.") from exc


def validate_html(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        raise ConversionFailed("The generated HTML is empty.")
    text = path.read_text("utf-8", errors="replace")
    if "<" not in text:
        raise ConversionFailed("The generated HTML is not valid HTML.")
    return len(text)
