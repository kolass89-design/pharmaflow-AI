"""Spreadsheet, presentation, CSV, text and HTML conversions."""

from __future__ import annotations

import csv
import html as html_lib
import io
import logging
import re
from html.parser import HTMLParser
from pathlib import Path

import pymupdf

from ..errors import ConversionFailed, EngineUnavailable, ValidationError
from . import validation as v
from .office_render import convert_with_libreoffice, libreoffice_available

log = logging.getLogger(__name__)


# --- Office -> PDF ----------------------------------------------------------


def _office_to_pdf(ctx, target_ext: str) -> list:
    source = ctx.files[0]
    if not libreoffice_available():
        raise EngineUnavailable(
            "Converting this format to PDF needs the LibreOffice renderer, which is not installed "
            "on this server. See the deployment guide to enable it.",
            code="libreoffice_unavailable",
        )
    ctx.report(0.15, "Rendering with LibreOffice")
    pdf_path = convert_with_libreoffice(source.path, ctx.workdir, target_ext, timeout=ctx.settings.conversion_timeout)
    pages = v.validate_pdf(pdf_path)
    target = ctx.outdir / f"{source.stem}.pdf"
    target.write_bytes(pdf_path.read_bytes())
    return [
        ctx.emit(
            target,
            f"{source.stem}.pdf",
            "application/pdf",
            meta={"pages": pages, "method": "libreoffice"},
        )
    ]


def xlsx_to_pdf(ctx) -> list:
    if libreoffice_available():
        return _office_to_pdf(ctx, "pdf")
    return xlsx_to_pdf_fallback(ctx)


def pptx_to_pdf(ctx) -> list:
    return _office_to_pdf(ctx, "pdf")


def csv_to_xlsx(ctx) -> list:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    source = ctx.files[0]
    raw = source.path.read_bytes()
    text = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:  # pragma: no cover - latin-1 always decodes
        raise ConversionFailed("The CSV file could not be decoded.")
    if not text.strip():
        raise ConversionFailed("The CSV file is empty.")

    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";" if sample.count(";") > sample.count(",") else ","

    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    rows = [row for row in rows if any(cell.strip() for cell in row)]
    if not rows:
        raise ConversionFailed("The CSV file contains no data rows.")
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    for r_index, row in enumerate(rows, start=1):
        for c_index, value in enumerate(row, start=1):
            value = value.strip()
            cell = ws.cell(row=r_index, column=c_index)
            if value == "":
                continue
            parsed: object = value
            if ctx.opt_bool("detect_numbers", True):
                normalised = value.replace(" ", "").replace("\u00a0", "")
                if re.fullmatch(r"-?\d{1,3}(?:[,.]\d{3})*(?:[,.]\d+)?|-?\d+(?:[,.]\d+)?", normalised):
                    candidate = normalised.replace(",", ".")
                    try:
                        parsed = float(candidate)
                        if parsed.is_integer() and "." not in candidate:
                            parsed = int(parsed)
                    except ValueError:
                        parsed = value
            cell.value = parsed
            if r_index == 1:
                cell.font = Font(bold=True)
    for column in ws.columns:
        width = max((len(str(cell.value or "")) for cell in column), default=8)
        ws.column_dimensions[column[0].column_letter].width = min(60, max(10, width + 2))
    ws.freeze_panes = "A2"
    target = ctx.outdir / "converted.xlsx"
    wb.save(str(target))
    sheets = v.validate_xlsx(target)
    return [
        ctx.emit(
            target,
            f"{source.stem}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            meta={"rows": len(rows), "columns": max(len(r) for r in rows), "sheets": sheets, "delimiter": delimiter},
        )
    ]


def xlsx_to_csv(ctx) -> list:
    from openpyxl import load_workbook

    source = ctx.files[0]
    try:
        wb = load_workbook(str(source.path), read_only=True, data_only=True)
    except Exception as exc:
        raise ConversionFailed("This spreadsheet could not be opened.") from exc
    outputs: list[Path] = []
    names: list[str] = []
    try:
        for index, sheet_name in enumerate(wb.sheetnames):
            ctx.check_cancel()
            ws = wb[sheet_name]
            target = ctx.outdir / f"sheet-{index + 1:03d}.csv"
            with target.open("w", encoding="utf-8", newline="") as fh:
                writer = csv.writer(fh)
                row_count = 0
                for row in ws.iter_rows(values_only=True):
                    if row is None:
                        continue
                    if all(cell is None or str(cell).strip() == "" for cell in row):
                        continue
                    writer.writerow(["" if cell is None else cell for cell in row])
                    row_count += 1
                    if row_count > 200_000:
                        raise ValidationError(
                            "This worksheet is too large to export (200,000 row limit).",
                            code="too_many_rows",
                        )
            if row_count == 0:
                target.unlink(missing_ok=True)
                continue
            v.validate_text(target)
            outputs.append(target)
            safe_sheet = re.sub(r"[^A-Za-z0-9._-]+", "-", sheet_name).strip("-") or f"sheet-{index + 1}"
            names.append(f"{source.stem}-{safe_sheet}.csv")
            ctx.report(0.1 + 0.8 * (index + 1) / max(1, len(wb.sheetnames)), f"Exported {sheet_name}")
    finally:
        wb.close()
    if not outputs:
        raise ConversionFailed("This spreadsheet contains no data to export.")
    if len(outputs) == 1:
        return [ctx.emit(outputs[0], names[0], "text/csv; charset=utf-8", meta={"sheets": 1})]
    from .common import make_zip

    archive = ctx.outdir / "sheets.zip"
    make_zip(outputs, archive, names)
    v.validate_zip(archive)
    return [
        ctx.emit(
            archive,
            f"{source.stem}-sheets.zip",
            "application/zip",
            meta={"files": len(outputs)},
        )
    ]


# --- text / HTML -> PDF -----------------------------------------------------


def _story_to_pdf(html: str, destination: Path, css: str, page: str = "a4", margin: float = 56.0) -> int:
    story = pymupdf.Story(html=html, user_css=css)
    writer = pymupdf.DocumentWriter(str(destination))
    page_rect = pymupdf.paper_rect(page)
    content = page_rect + (margin, margin, -margin, -margin)
    more = 1
    pages = 0
    try:
        while more:
            device = writer.begin_page(page_rect)
            more, _ = story.place(content)
            story.draw(device)
            writer.end_page()
            pages += 1
            if pages > 2000:
                break
    finally:
        writer.close()
    v.validate_pdf(destination)
    return pages


_TEXT_CSS = """
body { font-family: 'DejaVu Sans', 'Liberation Sans', sans-serif; font-size: 10.5pt;
       line-height: 1.5; color: #111827; }
p { margin: 0 0 8pt 0; white-space: pre-wrap; }
h1 { font-size: 15pt; margin: 0 0 10pt 0; }
"""


def text_to_pdf(ctx) -> list:
    source = ctx.files[0]
    raw = source.path.read_bytes()
    text = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:  # pragma: no cover
        raise ConversionFailed("The text file could not be decoded.")
    text = text.strip()
    if not text:
        raise ConversionFailed("The text file is empty.")
    if len(text) > 5_000_000:
        raise ValidationError("The text file is too large to convert (5 MB of text maximum).", code="too_large")
    paragraphs = [p for p in re.split(r"\n\s*\n", text)]
    body = "\n".join(f"<p>{html_lib.escape(p).replace(chr(10), '<br/>')}</p>" for p in paragraphs if p.strip())
    html = f"<h1>{html_lib.escape(source.stem)}</h1>{body}"
    target = ctx.outdir / f"{source.stem}.pdf"
    ctx.report(0.3, "Laying out text")
    pages = _story_to_pdf(html, target, _TEXT_CSS, page=str(ctx.opt("page_size", "a4")))
    return [
        ctx.emit(
            target,
            f"{source.stem}.pdf",
            "application/pdf",
            meta={"pages": pages, "characters": len(text), "method": "html-layout"},
        )
    ]


class _Sanitizer(HTMLParser):
    """Strip active content and remote references from user supplied HTML."""

    BLOCKED = {"script", "iframe", "object", "embed", "form", "input", "button", "link", "meta", "base"}
    VOID = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
    ALLOWED_ATTRS = {"class", "style", "colspan", "rowspan", "href", "alt", "width", "height", "align"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.BLOCKED:
            if tag not in self.VOID:
                self.skip_depth += 1
            return
        if self.skip_depth:
            return
        kept = []
        for name, value in attrs:
            if name.lower().startswith("on"):
                continue
            if name.lower() in {"src", "srcset", "poster"}:
                continue
            if name.lower() in self.ALLOWED_ATTRS and value is not None:
                kept.append(f'{name}="{html_lib.escape(value, quote=True)}"')
        self.out.append(f"<{tag}{(' ' + ' '.join(kept)) if kept else ''}>")

    def handle_startendtag(self, tag, attrs):
        if tag in self.BLOCKED:
            return
        if self.skip_depth:
            return
        kept = []
        for name, value in attrs:
            if name.lower().startswith("on") or name.lower() in {"src", "srcset", "poster"}:
                continue
            if name.lower() in self.ALLOWED_ATTRS and value is not None:
                kept.append(f'{name}="{html_lib.escape(value, quote=True)}"')
        self.out.append(f"<{tag}{(' ' + ' '.join(kept)) if kept else ''}/>")

    def handle_endtag(self, tag):
        if tag in self.BLOCKED:
            if tag not in self.VOID:
                self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return
        self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.skip_depth:
            self.out.append(html_lib.escape(data, quote=False))

    def result(self) -> str:
        return "".join(self.out)


_HTML_CSS = """
body { font-family: 'DejaVu Sans', 'Liberation Sans', sans-serif; font-size: 10.5pt;
       line-height: 1.5; color: #111827; }
h1,h2,h3,h4 { color: #0f172a; margin: 12pt 0 6pt 0; }
p { margin: 0 0 7pt 0; }
table { border-collapse: collapse; margin: 8pt 0; width: 100%; }
td, th { border: 0.6pt solid #cbd5e1; padding: 4pt 6pt; vertical-align: top; }
th { background: #f1f5f9; }
blockquote { margin: 8pt 16pt; color: #475569; }
pre, code { font-family: 'DejaVu Sans Mono', monospace; font-size: 9pt; }
"""


def html_to_pdf(ctx) -> list:
    source = ctx.files[0]
    raw = source.path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    if not text.strip():
        raise ConversionFailed("The HTML file is empty.")
    if len(text) > 5_000_000:
        raise ValidationError("The HTML file is too large to convert.", code="too_large")
    sanitizer = _Sanitizer()
    try:
        sanitizer.feed(text)
        sanitizer.close()
    except Exception as exc:
        raise ConversionFailed("The HTML file could not be parsed.") from exc
    body = sanitizer.result()
    if not body.strip():
        raise ConversionFailed("The HTML file contains no renderable content.")
    target = ctx.outdir / f"{source.stem}.pdf"
    ctx.report(0.3, "Laying out page")
    pages = _story_to_pdf(body, target, _HTML_CSS, page=str(ctx.opt("page_size", "a4")))
    return [
        ctx.emit(
            target,
            f"{source.stem}.pdf",
            "application/pdf",
            meta={
                "pages": pages,
                "method": "html-layout",
                "notes": [
                    "External images, scripts and remote stylesheets are not loaded for privacy and "
                    "security; embedded images and inline styles are preserved."
                ],
            },
        )
    ]


def xlsx_to_pdf_fallback(ctx) -> list:
    """Tabular PDF rendering used when LibreOffice is unavailable."""
    from openpyxl import load_workbook

    source = ctx.files[0]
    max_rows = 2000
    max_cols = 40
    try:
        wb = load_workbook(str(source.path), read_only=True, data_only=True)
    except Exception as exc:
        raise ConversionFailed("This spreadsheet could not be opened.") from exc
    sections: list[str] = []
    try:
        for sheet_name in wb.sheetnames[:10]:
            ws = wb[sheet_name]
            rows_html: list[str] = []
            for r_index, row in enumerate(ws.iter_rows(values_only=True)):
                if r_index >= max_rows:
                    rows_html.append(
                        f'<tr><td colspan="{max_cols}"><em>Rows beyond {max_rows} are not included '
                        f"in this PDF.</em></td></tr>"
                    )
                    break
                cells = list(row[:max_cols])
                if all(c is None or str(c).strip() == "" for c in cells):
                    continue
                tag = "th" if r_index == 0 else "td"
                rows_html.append(
                    "<tr>"
                    + "".join(f"<{tag}>{html_lib.escape('' if c is None else str(c))}</{tag}>" for c in cells)
                    + "</tr>"
                )
            if rows_html:
                sections.append(f"<h2>{html_lib.escape(sheet_name)}</h2><table>{''.join(rows_html)}</table>")
    finally:
        wb.close()
    if not sections:
        raise ConversionFailed("This spreadsheet contains no data to render.")
    html = "".join(sections)
    target = ctx.outdir / f"{source.stem}.pdf"
    ctx.report(0.4, "Laying out worksheet")
    pages = _story_to_pdf(
        html,
        target,
        _HTML_CSS + "body{font-size:8.5pt} td,th{padding:2pt 4pt}",
        page="a4-l",
        margin=32.0,
    )
    return [
        ctx.emit(
            target,
            f"{source.stem}.pdf",
            "application/pdf",
            meta={
                "pages": pages,
                "method": "html-layout",
                "notes": [f"Up to {max_rows} rows and {max_cols} columns per sheet are rendered."],
            },
        )
    ]
