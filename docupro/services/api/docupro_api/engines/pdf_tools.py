"""PDF page operations: merge, split, extract, delete, reorder, rotate,
compress, protect/unlock, page numbering and watermarking."""

from __future__ import annotations

import logging
from pathlib import Path

import pymupdf

from ..errors import ConversionFailed, ValidationError
from . import validation as v
from .common import (
    clamp,
    complement_pages,
    copy_pages,
    make_zip,
    open_pdf,
    parse_page_selection,
    require_page_budget,
)

log = logging.getLogger(__name__)

PDF_MIME = "application/pdf"


def _save(doc: pymupdf.Document, path: Path, *, garbage: int = 4) -> None:
    try:
        doc.save(
            path,
            garbage=garbage,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True,
            clean=True,
        )
    except Exception as exc:  # pragma: no cover - defensive
        raise ConversionFailed("The PDF could not be written. Try a different option set.") from exc


def _stamp_metadata(doc: pymupdf.Document) -> None:
    meta = doc.metadata or {}
    meta.update({"producer": "DOCUPRO", "creator": "DOCUPRO"})
    try:
        doc.set_metadata(meta)
    except Exception:  # pragma: no cover
        pass


# --- merge ------------------------------------------------------------------


def merge_pdf(ctx) -> list:
    ctx.report(0.05, "Reading documents")
    out = pymupdf.open()
    toc: list[list] = []
    total_pages = 0
    for index, src in enumerate(ctx.files):
        ctx.check_cancel()
        with open_pdf(src.path) as doc:
            require_page_budget(doc.page_count, ctx.settings)
            start_page = out.page_count + 1
            out.insert_pdf(doc)
            total_pages += doc.page_count
            if ctx.opt_bool("add_bookmarks", True):
                toc.append([1, src.stem[:120], start_page])
        ctx.report(0.1 + 0.75 * (index + 1) / len(ctx.files), f"Merged {index + 1} of {len(ctx.files)}")
    require_page_budget(total_pages, ctx.settings)
    if toc and len(toc) > 1:
        try:
            out.set_toc(toc)
        except Exception:  # pragma: no cover
            pass
    _stamp_metadata(out)
    target = ctx.outdir / "merged.pdf"
    _save(out, target)
    out.close()
    pages = v.validate_pdf(target)
    ctx.report(0.98, "Validating output")
    return [
        ctx.emit(
            target,
            f"{ctx.files[0].stem}-merged.pdf",
            PDF_MIME,
            meta={"pages": pages, "sources": len(ctx.files)},
        )
    ]


# --- split / extract / delete ----------------------------------------------


def split_pdf(ctx) -> list:
    mode = str(ctx.opt("split_mode", "each"))
    with open_pdf(ctx.files[0].path) as doc:
        require_page_budget(doc.page_count, ctx.settings)
        page_count = doc.page_count
        groups: list[list[int]] = []
        if mode == "chunks":
            size = ctx.opt_int("chunk_size", 10, 1, ctx.settings.max_pages)
            groups = [list(range(i, min(i + size, page_count))) for i in range(0, page_count, size)]
        elif mode == "ranges":
            raw = str(ctx.opt("ranges", ""))
            if not raw.strip():
                raise ValidationError("Enter at least one page range, for example 1-3.", code="invalid_pages")
            groups = []
            for part in raw.split(";"):
                if part.strip():
                    groups.append(parse_page_selection(part, page_count))
        else:
            groups = [[i] for i in range(page_count)]

        outputs: list[Path] = []
        names: list[str] = []
        stem = ctx.files[0].stem
        for index, group in enumerate(groups):
            ctx.check_cancel()
            part = copy_pages(doc, group)
            _stamp_metadata(part)
            if len(group) == 1:
                name = f"{stem}-page-{group[0] + 1:03d}.pdf"
            else:
                name = f"{stem}-pages-{group[0] + 1:03d}-{group[-1] + 1:03d}.pdf"
            target = ctx.outdir / f"split-{index + 1:04d}.pdf"
            _save(part, target, garbage=2)
            part.close()
            v.validate_pdf(target)
            outputs.append(target)
            names.append(name)
            ctx.report(0.1 + 0.8 * (index + 1) / max(1, len(groups)), f"Wrote {index + 1} of {len(groups)} files")

        if len(outputs) == 1:
            return [ctx.emit(outputs[0], names[0], PDF_MIME, meta={"pages": len(groups[0])})]

        archive = ctx.outdir / "split.zip"
        make_zip(outputs, archive, names)
        v.validate_zip(archive)
        return [
            ctx.emit(
                archive,
                f"{stem}-split.zip",
                "application/zip",
                meta={"files": len(outputs), "pages": page_count},
            )
        ]


def extract_pages(ctx) -> list:
    with open_pdf(ctx.files[0].path) as doc:
        require_page_budget(doc.page_count, ctx.settings)
        selection = parse_page_selection(ctx.opt("pages", ""), doc.page_count)
        out = copy_pages(doc, selection)
    _stamp_metadata(out)
    target = ctx.outdir / "extracted.pdf"
    _save(out, target)
    out.close()
    v.validate_pdf(target)
    return [
        ctx.emit(
            target,
            f"{ctx.files[0].stem}-pages.pdf",
            PDF_MIME,
            meta={"pages": len(selection), "selected": [p + 1 for p in selection]},
        )
    ]


def delete_pages(ctx) -> list:
    with open_pdf(ctx.files[0].path) as doc:
        require_page_budget(doc.page_count, ctx.settings)
        to_remove = parse_page_selection(ctx.opt("pages", ""), doc.page_count)
        kept = complement_pages(doc.page_count, to_remove)
        out = copy_pages(doc, kept)
    _stamp_metadata(out)
    target = ctx.outdir / "deleted.pdf"
    _save(out, target)
    out.close()
    v.validate_pdf(target)
    return [
        ctx.emit(
            target,
            f"{ctx.files[0].stem}-cleaned.pdf",
            PDF_MIME,
            meta={"pages": len(kept), "removed": len(to_remove)},
        )
    ]


def reorder_pages(ctx) -> list:
    with open_pdf(ctx.files[0].path) as doc:
        require_page_budget(doc.page_count, ctx.settings)
        order = parse_page_selection(ctx.opt("pages", ""), doc.page_count)
        if set(order) != set(range(doc.page_count)) or len(order) != doc.page_count:
            raise ValidationError(
                "The new order must list every page exactly once (use e.g. 3,1,2).",
                code="invalid_pages",
            )
        out = copy_pages(doc, order)
    _stamp_metadata(out)
    target = ctx.outdir / "reordered.pdf"
    _save(out, target)
    out.close()
    v.validate_pdf(target)
    return [
        ctx.emit(
            target,
            f"{ctx.files[0].stem}-reordered.pdf",
            PDF_MIME,
            meta={"pages": len(order), "order": [p + 1 for p in order]},
        )
    ]


# --- rotate -----------------------------------------------------------------


def rotate_pages(ctx) -> list:
    angle = ctx.opt_int("angle", 90)
    if angle not in {90, 180, 270}:
        raise ValidationError("Rotation must be 90, 180 or 270 degrees.", code="invalid_option")
    with open_pdf(ctx.files[0].path) as doc:
        require_page_budget(doc.page_count, ctx.settings)
        selection = parse_page_selection(ctx.opt("pages", ""), doc.page_count)
        for idx in selection:
            ctx.check_cancel()
            page = doc.load_page(idx)
            page.set_rotation((page.rotation + angle) % 360)
        _stamp_metadata(doc)
        target = ctx.outdir / "rotated.pdf"
        _save(doc, target)
    v.validate_pdf(target)
    return [
        ctx.emit(
            target,
            f"{ctx.files[0].stem}-rotated.pdf",
            PDF_MIME,
            meta={"pages": len(selection), "angle": angle},
        )
    ]


# --- compression ------------------------------------------------------------


_PRESETS = {
    "light": {"quality": 82, "dpi": 220},
    "balanced": {"quality": 68, "dpi": 150},
    "strong": {"quality": 48, "dpi": 110},
}


def compress_pdf(ctx) -> list:
    preset = str(ctx.opt("preset", "balanced"))
    if preset not in _PRESETS:
        raise ValidationError("Unknown compression preset.", code="invalid_option")
    config = _PRESETS[preset]
    source = ctx.files[0]
    with open_pdf(source.path) as doc:
        require_page_budget(doc.page_count, ctx.settings)
        ctx.report(0.2, "Optimising images")
        try:
            doc.rewrite_images(
                dpi_target=config["dpi"],
                dpi_threshold=config["dpi"] + 10,
                quality=config["quality"],
                lossy=True,
                color=True,
                gray=True,
                bitonal=True,
            )
        except Exception as exc:  # pragma: no cover - engine dependent
            log.warning("Image rewriting unavailable: %s", exc)
        ctx.report(0.6, "Subsetting fonts")
        try:
            doc.subset_fonts(verbose=False)
        except Exception:  # pragma: no cover
            pass
        _stamp_metadata(doc)
        target = ctx.outdir / "compressed.pdf"
        _save(doc, target)
    pages = v.validate_pdf(target)
    original = source.size
    new_size = target.stat().st_size
    ctx.report(0.95, "Comparing sizes")
    return [
        ctx.emit(
            target,
            f"{source.stem}-compressed.pdf",
            PDF_MIME,
            meta={
                "pages": pages,
                "originalSize": original,
                "compressedSize": new_size,
                "savedPercent": round(max(0.0, 1 - new_size / original) * 100, 1) if original else 0,
                "preset": preset,
            },
        )
    ]


# --- protection -------------------------------------------------------------

_PERMISSION_SETS = {
    "view": pymupdf.PDF_PERM_ACCESSIBILITY,
    "print": pymupdf.PDF_PERM_ACCESSIBILITY | pymupdf.PDF_PERM_PRINT,
    "all": pymupdf.PDF_PERM_ACCESSIBILITY | pymupdf.PDF_PERM_PRINT | pymupdf.PDF_PERM_COPY | pymupdf.PDF_PERM_ANNOTATE,
}


def protect_pdf(ctx) -> list:
    password = str(ctx.opt("password", ""))
    if len(password) < 4:
        raise ValidationError("Choose a password of at least 4 characters.", code="invalid_option")
    if len(password) > 128:
        raise ValidationError("The password is too long (128 characters maximum).", code="invalid_option")
    owner = str(ctx.opt("owner_password", "") or "")
    if owner and len(owner) < 4:
        raise ValidationError("The owner password is too short.", code="invalid_option")
    permissions = str(ctx.opt("permissions", "print"))
    if permissions not in _PERMISSION_SETS:
        raise ValidationError("Unknown permission profile.", code="invalid_option")

    with open_pdf(ctx.files[0].path) as doc:
        require_page_budget(doc.page_count, ctx.settings)
        _stamp_metadata(doc)
        target = ctx.outdir / "protected.pdf"
        doc.save(
            target,
            encryption=pymupdf.PDF_ENCRYPT_AES_256,
            owner_pw=owner or password,
            user_pw=password,
            permissions=_PERMISSION_SETS[permissions],
            garbage=3,
            deflate=True,
        )
    # Validate by reopening with the password.
    try:
        check = pymupdf.open(target)
        if not check.needs_pass or not check.authenticate(password):
            raise ConversionFailed("The encrypted PDF could not be verified.")
        pages = check.page_count
        check.close()
    except ConversionFailed:
        raise
    except Exception as exc:  # pragma: no cover
        raise ConversionFailed("The encrypted PDF could not be verified.") from exc
    return [
        ctx.emit(
            target,
            f"{ctx.files[0].stem}-protected.pdf",
            PDF_MIME,
            meta={"pages": pages, "encryption": "AES-256", "permissions": permissions},
        )
    ]


def unlock_pdf(ctx) -> list:
    password = str(ctx.opt("password", "") or "")
    try:
        doc = pymupdf.open(ctx.files[0].path)
    except Exception as exc:
        raise ConversionFailed("This PDF could not be opened.") from exc
    if not doc.needs_pass:
        pages = doc.page_count
        doc.close()
        raise ValidationError(
            "This PDF is not password protected, so there is nothing to unlock.",
            code="not_encrypted",
            details={"pages": pages},
        )
    if not doc.authenticate(password):
        doc.close()
        raise ValidationError(
            "That password is not valid for this document.",
            code="invalid_password",
        )
    _stamp_metadata(doc)
    target = ctx.outdir / "unlocked.pdf"
    try:
        doc.save(target, encryption=pymupdf.PDF_ENCRYPT_NONE, garbage=3, deflate=True)
    finally:
        doc.close()
    pages = v.validate_pdf(target)
    return [
        ctx.emit(
            target,
            f"{ctx.files[0].stem}-unlocked.pdf",
            PDF_MIME,
            meta={"pages": pages, "encryption": "none"},
        )
    ]


# --- page numbers / watermarks ---------------------------------------------


def add_page_numbers(ctx) -> list:
    position = str(ctx.opt("position", "bottom-center"))
    style = str(ctx.opt("style", "n"))
    start_at = ctx.opt_int("start_at", 1, 0, 100000)
    font_size = clamp(ctx.opt_float("font_size", 10.0), 6, 36)
    with open_pdf(ctx.files[0].path) as doc:
        require_page_budget(doc.page_count, ctx.settings)
        total = doc.page_count
        for idx in range(total):
            ctx.check_cancel()
            page = doc.load_page(idx)
            number = start_at + idx
            if style == "n-of-total":
                text = f"{number} / {total}"
            elif style == "page-n":
                text = f"Page {number} of {total}"
            elif style == "dash":
                text = f"- {number} -"
            else:
                text = str(number)
            width, height = page.rect.width, page.rect.height
            margin = 28.0
            if position.startswith("bottom"):
                y0, y1 = height - margin - font_size, height - margin + 2
            else:
                y0, y1 = margin - 2, margin + font_size + 2
            if position.endswith("left"):
                x0, x1 = margin, width / 2
                align = pymupdf.TEXT_ALIGN_LEFT
            elif position.endswith("right"):
                x0, x1 = width / 2, width - margin
                align = pymupdf.TEXT_ALIGN_RIGHT
            else:
                x0, x1 = margin, width - margin
                align = pymupdf.TEXT_ALIGN_CENTER
            page.insert_textbox(
                pymupdf.Rect(x0, y0, x1, y1),
                text,
                fontsize=font_size,
                fontname="helv",
                color=(0.25, 0.25, 0.3),
                align=align,
            )
        _stamp_metadata(doc)
        target = ctx.outdir / "numbered.pdf"
        _save(doc, target)
    pages = v.validate_pdf(target)
    return [
        ctx.emit(
            target,
            f"{ctx.files[0].stem}-numbered.pdf",
            PDF_MIME,
            meta={"pages": pages, "style": style, "position": position},
        )
    ]


def watermark_pdf(ctx) -> list:
    text = str(ctx.opt("text", "CONFIDENTIAL")).strip()[:200]
    if not text:
        raise ValidationError("Enter the watermark text.", code="invalid_option")
    opacity = clamp(ctx.opt_float("opacity", 0.18), 0.03, 1.0)
    angle = clamp(ctx.opt_float("angle", 45), -90, 90)
    font_size = clamp(ctx.opt_float("font_size", 54), 8, 220)
    layout = str(ctx.opt("layout", "diagonal"))
    try:
        color_hex = str(ctx.opt("color", "#94a3b8")).lstrip("#")
        color = tuple(int(color_hex[i : i + 2], 16) / 255 for i in (0, 2, 4))
    except (ValueError, IndexError):
        color = (0.58, 0.64, 0.7)

    with open_pdf(ctx.files[0].path) as doc:
        require_page_budget(doc.page_count, ctx.settings)
        selection = set(parse_page_selection(ctx.opt("pages", ""), doc.page_count))
        font = pymupdf.Font("hebo")
        for idx in range(doc.page_count):
            if idx not in selection:
                continue
            ctx.check_cancel()
            page = doc.load_page(idx)
            rect = page.rect
            writer = pymupdf.TextWriter(rect)
            if layout == "footer":
                size = min(font_size, 28)
                width = font.text_length(text, fontsize=size)
                pos = pymupdf.Point((rect.width - width) / 2, rect.height - 24)
                writer.append(pos, text, font=font, fontsize=size)
                writer.write_text(page, color=color, opacity=max(opacity, 0.35), overlay=True)
            else:
                width = font.text_length(text, fontsize=font_size)
                pos = pymupdf.Point(rect.width / 2 - width / 2, rect.height / 2 + font_size / 3)
                writer.append(pos, text, font=font, fontsize=font_size)
                pivot = pymupdf.Point(rect.width / 2, rect.height / 2)
                matrix = pymupdf.Matrix(angle)
                writer.write_text(
                    page,
                    color=color,
                    opacity=opacity,
                    overlay=True,
                    morph=(pivot, matrix),
                )
        _stamp_metadata(doc)
        target = ctx.outdir / "watermarked.pdf"
        _save(doc, target)
    pages = v.validate_pdf(target)
    return [
        ctx.emit(
            target,
            f"{ctx.files[0].stem}-watermarked.pdf",
            PDF_MIME,
            meta={"pages": pages, "text": text, "layout": layout},
        )
    ]
