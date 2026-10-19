"""Conversions for Microsoft Word documents (.docx and legacy .doc)."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from ..errors import ConversionFailed, EngineUnavailable
from . import validation as v
from .common import open_pdf, render_page_bytes
from .office_render import convert_with_libreoffice, libreoffice_available

log = logging.getLogger(__name__)
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _render_to_pdf(ctx, source: Path, timeout: int) -> tuple[Path, str]:
    """Return (pdf_path, method) using the best available renderer."""
    if libreoffice_available() and ctx.opt_bool("prefer_libreoffice", True):
        ctx.report(0.15, "Rendering with LibreOffice")
        pdf_path = convert_with_libreoffice(source, ctx.workdir, "pdf", timeout=timeout)
        return pdf_path, "libreoffice"
    if source.suffix.lower() == ".docx":
        ctx.report(0.15, "Rendering document structure")
        target = ctx.workdir / f"{source.stem}-rendered.pdf"
        from .docx_render import render as render_docx

        info = render_docx(source, target, ctx.workdir)
        return target, info.method
    raise EngineUnavailable(
        "This file type needs the LibreOffice renderer, which is not installed on this server.",
        code="libreoffice_unavailable",
    )


def word_to_pdf(ctx) -> list:
    source = ctx.files[0]
    if source.path.suffix.lower() == ".doc" and not libreoffice_available():
        raise EngineUnavailable(
            "Legacy .doc files need LibreOffice on the server. Save the file as .docx and try again.",
            code="libreoffice_unavailable",
        )
    pdf_path, method = _render_to_pdf(ctx, source.path, ctx.settings.conversion_timeout)
    ctx.report(0.85, "Validating output")
    pages = v.validate_pdf(pdf_path)
    target = ctx.outdir / f"{source.stem}.pdf"
    target.write_bytes(pdf_path.read_bytes())
    notes = []
    if method != "libreoffice":
        notes.append(
            "Rendered with the built-in engine: headings, lists, tables, images, page breaks, headers, "
            "footers and page numbers are preserved, but exact Word pagination may differ."
        )
    return [
        ctx.emit(
            target,
            f"{source.stem}.pdf",
            "application/pdf",
            meta={"pages": pages, "method": method, "notes": notes},
        )
    ]


def word_to_images(ctx, fmt: str) -> list:
    source = ctx.files[0]
    dpi = ctx.opt_int("dpi", 150, 70, 400)
    if source.path.suffix.lower() == ".doc" and not libreoffice_available():
        raise EngineUnavailable(
            "Legacy .doc files need LibreOffice on the server. Save the file as .docx and try again.",
            code="libreoffice_unavailable",
        )
    pdf_path, method = _render_to_pdf(ctx, source.path, ctx.settings.conversion_timeout)
    ext = "jpg" if fmt == "jpeg" else "png"
    media = "image/jpeg" if fmt == "jpeg" else "image/png"
    outputs: list[Path] = []
    names: list[str] = []
    with open_pdf(pdf_path) as doc:
        total = doc.page_count
        if total > ctx.settings.max_pages:
            raise ConversionFailed("The document produced too many pages to render.")
        for index in range(total):
            ctx.check_cancel()
            page = doc.load_page(index)
            data, width, height = render_page_bytes(page, dpi, fmt, ctx.settings.max_pixels)
            target = ctx.outdir / f"page-{index + 1:04d}.{ext}"
            target.write_bytes(data)
            v.validate_image(target, expected_format=fmt)
            outputs.append(target)
            names.append(f"{source.stem}-page-{index + 1:03d}.{ext}")
            ctx.report(0.5 + 0.45 * (index + 1) / total, f"Rendering page {index + 1} of {total}")
    meta = {"pages": len(outputs), "dpi": dpi, "width": width, "height": height, "method": method}
    if len(outputs) == 1:
        return [ctx.emit(outputs[0], names[0], media, meta=meta)]
    if not ctx.opt_bool("zip", True):
        return [
            ctx.emit(path, name, media, meta={"page": i + 1, "dpi": dpi})
            for i, (path, name) in enumerate(zip(outputs, names))
        ]
    from .common import make_zip

    archive = ctx.outdir / "pages.zip"
    make_zip(outputs, archive, names)
    v.validate_zip(archive)
    return [
        ctx.emit(
            archive,
            f"{source.stem}-{ext}.zip",
            "application/zip",
            meta={**meta, "files": len(outputs)},
        )
    ]


def word_to_jpeg(ctx) -> list:
    return word_to_images(ctx, "jpeg")


def word_to_png(ctx) -> list:
    return word_to_images(ctx, "png")


def _iter_block_items(document):
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    parent = document.element.body
    for child in parent.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


def word_to_text(ctx) -> list:
    import docx

    source = ctx.files[0]
    if source.path.suffix.lower() == ".doc":
        if not libreoffice_available():
            raise EngineUnavailable(
                "Legacy .doc files need LibreOffice on the server. Save the file as .docx and try again.",
                code="libreoffice_unavailable",
            )
        rendered = convert_with_libreoffice(source.path, ctx.workdir, "txt")
        text = rendered.read_text("utf-8", errors="replace")
    else:
        try:
            document = docx.Document(str(source.path))
        except Exception as exc:
            raise ConversionFailed("This Word document could not be opened.") from exc
        parts: list[str] = []
        for block in _iter_block_items(document):
            if hasattr(block, "rows"):
                for row in block.rows:
                    cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                    if any(cells):
                        parts.append("\t".join(cells))
                parts.append("")
            else:
                text = block.text
                style = (block.style.name or "").lower() if block.style is not None else ""
                if text.strip():
                    parts.append(text)
                elif parts:
                    parts.append("")
                if style.startswith("heading") and text.strip():
                    parts.insert(len(parts) - 1, "")
        text = "\n".join(parts)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        raise ConversionFailed("This Word document contains no readable text.")
    target = ctx.outdir / "document.txt"
    target.write_text(text + "\n", encoding="utf-8")
    v.validate_text(target)
    return [
        ctx.emit(
            target,
            f"{source.stem}.txt",
            "text/plain; charset=utf-8",
            meta={"characters": len(text), "words": len(text.split())},
        )
    ]


_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
:root {{ color-scheme: light; }}
body {{ margin: 0; padding: 48px 24px; background: #f8fafc; color: #111827;
       font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
main {{ max-width: 820px; margin: 0 auto; background: #fff; padding: 56px 64px;
       border-radius: 14px; box-shadow: 0 1px 3px rgba(15,23,42,.08), 0 12px 32px rgba(15,23,42,.06); }}
h1,h2,h3,h4 {{ color: #0f172a; line-height: 1.25; }}
p {{ line-height: 1.65; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
td, th {{ border: 1px solid #e2e8f0; padding: 8px 10px; text-align: left; vertical-align: top; }}
th {{ background: #f1f5f9; }}
img {{ max-width: 100%; height: auto; border-radius: 6px; }}
blockquote {{ border-left: 3px solid #cbd5e1; margin: 16px 0; padding: 4px 18px; color: #475569; }}
code, pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; background: #f1f5f9; }}
pre {{ padding: 14px; border-radius: 8px; overflow-x: auto; }}
@media (max-width: 640px) {{ body {{ padding: 16px; }} main {{ padding: 24px; border-radius: 10px; }} }}
</style>
</head>
<body><main>{body}</main></body></html>
"""


def word_to_html(ctx) -> list:
    from html import escape

    import mammoth

    source = ctx.files[0]
    if source.path.suffix.lower() == ".doc":
        raise EngineUnavailable(
            "HTML export is available for .docx files. Convert the .doc file to .docx first.",
            code="unsupported_legacy",
        )
    try:
        with source.path.open("rb") as fh:
            result = mammoth.convert_to_html(fh)
    except Exception as exc:
        raise ConversionFailed("This Word document could not be converted to HTML.") from exc
    body = result.value
    if not body.strip():
        raise ConversionFailed("This Word document contains no content to export.")
    html = _HTML_TEMPLATE.format(title=escape(source.stem), body=body)
    target = ctx.outdir / "document.html"
    target.write_text(html, encoding="utf-8")
    v.validate_html(target)
    warnings = [m.message for m in (result.messages or [])][:5]
    return [
        ctx.emit(
            target,
            f"{source.stem}.html",
            "text/html; charset=utf-8",
            meta={"characters": len(body), "warnings": warnings},
        )
    ]


def word_batch_to_pdf(ctx) -> list:
    """Convert several Word documents to PDF in one job."""
    outputs: list[Path] = []
    names: list[str] = []
    for index, source in enumerate(ctx.files):
        ctx.check_cancel()
        pdf_path, _ = _render_to_pdf(ctx, source.path, ctx.settings.conversion_timeout)
        v.validate_pdf(pdf_path)
        target = ctx.outdir / f"doc-{index + 1:03d}.pdf"
        target.write_bytes(pdf_path.read_bytes())
        outputs.append(target)
        names.append(f"{source.stem}.pdf")
        ctx.report(0.05 + 0.9 * (index + 1) / len(ctx.files), f"Converted {index + 1} of {len(ctx.files)}")
    from .common import make_zip

    if len(outputs) == 1:
        return [ctx.emit(outputs[0], names[0], "application/pdf", meta={"pages": v.validate_pdf(outputs[0])})]
    archive = ctx.outdir / "word-to-pdf.zip"
    make_zip(outputs, archive, names)
    v.validate_zip(archive)
    return [ctx.emit(archive, "word-to-pdf.zip", "application/zip", meta={"files": len(outputs)})]
