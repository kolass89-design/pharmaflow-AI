"""Shared helpers used by the conversion engines."""

from __future__ import annotations

import io
import re
import zipfile
from collections.abc import Iterable, Sequence
from pathlib import Path

import pymupdf
from PIL import Image, ImageOps

from ..errors import ConversionFailed, ValidationError

# Page geometry in PostScript points (1/72 inch).
PAGE_SIZES: dict[str, tuple[float, float]] = {
    "a4": (595.28, 841.89),
    "letter": (612.0, 792.0),
    "legal": (612.0, 1008.0),
    "a3": (841.89, 1190.55),
    "a5": (419.53, 595.28),
}

MM = 72.0 / 25.4
IMAGE_DPI_FALLBACK = 96.0

_RANGE_PART = re.compile(r"^\s*(\d+)?\s*(?:-\s*(\d+)?)?\s*$")


def parse_page_selection(spec: str | int | None, page_count: int) -> list[int]:
    """Parse a page selection such as ``1-3,5,8-`` into 0-based indexes.

    An empty value selects every page. Order is preserved and duplicates are
    dropped. Out-of-range pages raise a validation error rather than being
    silently ignored, so users always know what happened.
    """
    if page_count <= 0:
        raise ConversionFailed("The document contains no pages.")
    if spec is None:
        return list(range(page_count))
    if isinstance(spec, int):
        spec = str(spec)
    text = spec.strip().lower()
    if text in {"", "all", "*", "toutes", "todos"}:
        return list(range(page_count))

    selected: list[int] = []
    seen: set[int] = set()
    for raw_part in text.replace(";", ",").split(","):
        part = raw_part.strip()
        if not part:
            continue
        match = _RANGE_PART.match(part)
        if not match:
            raise ValidationError(
                "Page selection must look like 1-3,5,7. Please check the page range.",
                code="invalid_pages",
            )
        start_raw, end_raw = match.group(1), match.group(2)
        is_range = "-" in part
        if start_raw is None and end_raw is None:
            raise ValidationError("Page selection contains an empty range.", code="invalid_pages")
        start = int(start_raw) if start_raw else 1
        end = int(end_raw) if end_raw else (page_count if is_range else start)
        if start < 1 or end < start or start > page_count:
            raise ValidationError(
                f"Page {start} is outside this document (it has {page_count} page{'s' if page_count != 1 else ''}).",
                code="invalid_pages",
            )
        end = min(end, page_count)
        for page in range(start, end + 1):
            idx = page - 1
            if idx not in seen:
                seen.add(idx)
                selected.append(idx)
    if not selected:
        raise ValidationError("No pages were selected.", code="invalid_pages")
    return selected


def complement_pages(page_count: int, selected: Iterable[int]) -> list[int]:
    drop = set(selected)
    remaining = [i for i in range(page_count) if i not in drop]
    if not remaining:
        raise ValidationError("You cannot delete every page of the document.", code="invalid_pages")
    return remaining


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def open_pdf(path: Path) -> pymupdf.Document:
    try:
        doc = pymupdf.open(path)
    except Exception as exc:
        raise ConversionFailed("This PDF could not be opened. It may be damaged or password protected.") from exc
    if doc.needs_pass:
        doc.close()
        raise ConversionFailed(
            "This PDF is password protected. Unlock it first, then try again.",
            code="password_required",
        )
    if doc.page_count == 0:
        doc.close()
        raise ConversionFailed("This PDF contains no pages.")
    return doc


def require_page_budget(page_count: int, settings) -> None:
    if page_count > settings.max_pages:
        raise ValidationError(
            f"This document has {page_count} pages; the limit is {settings.max_pages}.",
            code="too_many_pages",
        )


def render_page_bytes(page: pymupdf.Page, dpi: int, image_format: str, max_pixels: int) -> tuple[bytes, int, int]:
    """Render one PDF page to bytes, respecting the pixel budget."""
    zoom = dpi / 72.0
    width = page.rect.width * zoom
    height = page.rect.height * zoom
    if width * height > max_pixels:
        raise ValidationError(
            "The requested resolution is too high for this page size. Try a lower DPI.",
            code="resolution_too_high",
        )
    matrix = pymupdf.Matrix(zoom, zoom)
    colorspace = pymupdf.csRGB
    pix = page.get_pixmap(matrix=matrix, colorspace=colorspace, alpha=False)
    fmt = "jpeg" if image_format.lower() in {"jpg", "jpeg"} else "png"
    data = pix.tobytes(fmt, jpg_quality=92) if fmt == "jpeg" else pix.tobytes(fmt)
    return data, pix.width, pix.height


def load_image(path: Path, max_pixels: int) -> Image.Image:
    """Open an image with decompression-bomb protection."""
    Image.MAX_IMAGE_PIXELS = max_pixels
    try:
        with Image.open(path) as probe:
            width, height = probe.size
            if width <= 0 or height <= 0:
                raise ValidationError("The image has invalid dimensions.", code="invalid_image")
            if width * height > max_pixels:
                raise ValidationError(
                    "The image resolution exceeds the allowed limit.",
                    code="image_too_large",
                )
            probe.load()
            img = ImageOps.exif_transpose(probe)
            return img.copy()
    except ValidationError:
        raise
    except Image.DecompressionBombError as exc:
        raise ValidationError("The image is too large to process safely.", code="image_too_large") from exc
    except Exception as exc:
        raise ConversionFailed("This image could not be read. It may be damaged.") from exc


def flatten_to_rgb(img: Image.Image, background: tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    if img.mode in {"RGBA", "LA", "P"}:
        rgba = img.convert("RGBA")
        canvas = Image.new("RGB", rgba.size, background)
        canvas.paste(rgba, mask=rgba.split()[-1])
        return canvas
    if img.mode == "CMYK":
        return img.convert("RGB")
    if img.mode not in {"RGB", "L"}:
        return img.convert("RGB")
    return img


def jpeg_bytes(img: Image.Image, quality: int = 85) -> bytes:
    buffer = io.BytesIO()
    flatten_to_rgb(img).save(buffer, format="JPEG", quality=int(clamp(quality, 30, 100)), optimize=True)
    return buffer.getvalue()


def png_bytes(img: Image.Image) -> bytes:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def image_page_size(img: Image.Image, page_size: str, orientation: str) -> tuple[float, float, float, float]:
    """Return (page_width, page_height, margin_points, dpi_hint) for a page."""
    dpi_meta = 96.0
    try:
        dpi_info = img.info.get("dpi")
        if dpi_info and float(dpi_info[0]) > 1:
            dpi_meta = float(dpi_info[0])
    except Exception:
        dpi_meta = IMAGE_DPI_FALLBACK

    if page_size == "fit":
        return (img.width * 72.0 / dpi_meta, img.height * 72.0 / dpi_meta, 0.0, dpi_meta)

    size = PAGE_SIZES.get(page_size, PAGE_SIZES["a4"])
    width, height = size
    if orientation == "portrait":
        width, height = min(width, height), max(width, height)
    elif orientation == "landscape":
        width, height = max(width, height), min(width, height)
    elif orientation == "auto":
        if img.width > img.height:
            width, height = max(width, height), min(width, height)
    return (width, height, 0.0, dpi_meta)


def fit_rect(
    img: Image.Image, page_w: float, page_h: float, margin_pt: float, fit_mode: str
) -> tuple[float, float, float, float]:
    """Compute the destination rectangle for an image on a page."""
    avail_w = max(1.0, page_w - 2 * margin_pt)
    avail_h = max(1.0, page_h - 2 * margin_pt)
    left, top = margin_pt, margin_pt
    if fit_mode == "stretch":
        return (left, top, left + avail_w, top + avail_h)
    img_ratio = img.width / max(1, img.height)
    box_ratio = avail_w / avail_h
    if fit_mode == "cover":
        if img_ratio > box_ratio:
            new_w, new_h = avail_w, avail_w / img_ratio
        else:
            new_h, new_w = avail_h, avail_h * img_ratio
    else:  # contain
        if img_ratio > box_ratio:
            new_w, new_h = avail_w, avail_w / img_ratio
        else:
            new_h, new_w = avail_h, avail_h * img_ratio
    x0 = left + (avail_w - new_w) / 2
    y0 = top + (avail_h - new_h) / 2
    return (x0, y0, x0 + new_w, y0 + new_h)


def crop_to_aspect(img: Image.Image, ratio: float) -> Image.Image:
    """Center-crop an image to the given width/height ratio (used for cover)."""
    current = img.width / max(1, img.height)
    if abs(current - ratio) < 1e-3:
        return img
    if current > ratio:
        new_w = int(round(img.height * ratio))
        left = (img.width - new_w) // 2
        return img.crop((left, 0, left + new_w, img.height))
    new_h = int(round(img.width / ratio))
    top = (img.height - new_h) // 2
    return img.crop((0, top, img.width, top + new_h))


def build_pdf_from_images(
    images: Sequence[Image.Image],
    page_size: str,
    orientation: str,
    margin_mm: float,
    fit_mode: str,
    quality: int,
) -> pymupdf.Document:
    doc = pymupdf.open()
    for img in images:
        page_w, page_h, _, _ = image_page_size(img, page_size, orientation)
        margin_pt = margin_mm * MM if page_size != "fit" else 0.0
        if page_size == "fit" and margin_mm > 0:
            margin_pt = margin_mm * MM
            page_w += 2 * margin_pt
            page_h += 2 * margin_pt
        page = doc.new_page(width=page_w, height=page_h)
        rect = fit_rect(img, page_w, page_h, margin_pt, fit_mode)
        target = img
        if fit_mode == "cover":
            ratio = (rect[2] - rect[0]) / max(1.0, rect[3] - rect[1])
            target = crop_to_aspect(img, ratio)
        data = jpeg_bytes(target, quality)
        page.insert_image(pymupdf.Rect(*rect), stream=data, keep_proportion=(fit_mode != "stretch"))
    return doc


def copy_pages(src: pymupdf.Document, indexes: Sequence[int]) -> pymupdf.Document:
    out = pymupdf.open()
    for idx in indexes:
        out.insert_pdf(src, from_page=idx, to_page=idx)
    return out


def add_zip_entry(zf: zipfile.ZipFile, path: Path, arcname: str) -> None:
    safe_name = re.sub(r"[\\/]+", "_", arcname)
    zf.write(path, arcname=safe_name)


def make_zip(paths: Iterable[Path], destination: Path, names: Iterable[str]) -> Path:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path, name in zip(paths, names):
            add_zip_entry(zf, path, name)
    return destination


def unique_name(base: str, used: set[str], extension: str = "") -> str:
    name = f"{base}{('.' + extension) if extension else ''}"
    if name not in used:
        used.add(name)
        return name
    counter = 2
    while True:
        candidate = f"{base} ({counter}){('.' + extension) if extension else ''}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        counter += 1


def number_to_words_placeholder() -> None:  # pragma: no cover
    """Kept for API stability; numbering uses digits only."""


#: Presentation-form ligatures that some PDF generators emit as single glyphs.
#: Extracted text such as "ﬁchier" breaks search, spell-check and screen readers,
#: so every text extraction path normalises them to plain letters.
LIGATURE_REPLACEMENTS = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\ufb05": "ft",
    "\ufb06": "st",
}


def normalize_ligatures(text: str) -> str:
    """Replace presentation-form ligatures with their plain letter sequences."""
    if not text:
        return text
    if not any(character in text for character in LIGATURE_REPLACEMENTS):
        return text
    for ligature, plain in LIGATURE_REPLACEMENTS.items():
        text = text.replace(ligature, plain)
    return text
