"""Unicode font discovery for text layers and fallback rendering."""

from __future__ import annotations

import functools
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

_CANDIDATES = (
    os.environ.get("DOCUPRO_FONT_PATH", ""),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    str(Path(__file__).resolve().parent.parent / "assets" / "DejaVuSans.ttf"),
)


@functools.lru_cache(maxsize=1)
def unicode_font_path() -> str | None:
    for candidate in _CANDIDATES:
        if candidate and Path(candidate).is_file():
            return candidate
    log.info("No Unicode TTF found; falling back to built-in fonts")
    return None


@functools.lru_cache(maxsize=4)
def load_font():
    """Return a PyMuPDF Font covering Latin, Greek, Cyrillic and Arabic, if possible."""
    import pymupdf

    path = unicode_font_path()
    if path:
        try:
            return pymupdf.Font(fontfile=path), path
        except Exception as exc:  # pragma: no cover - defensive
            log.warning("Could not load Unicode font %s: %s", path, exc)
    return pymupdf.Font("helv"), "helv"


def page_font_alias(page) -> tuple[str, object] | tuple[None, None]:
    """Register the Unicode font on a page once and return its alias."""
    import pymupdf

    font, path = load_font()
    if path == "helv":
        return "helv", font
    alias = "dprunicode"
    try:
        page.insert_font(fontname=alias, fontfile=path)
        return alias, font
    except Exception:  # pragma: no cover - defensive
        return "helv", pymupdf.Font("helv")
