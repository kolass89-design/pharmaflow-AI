"""Office document rendering.

LibreOffice is used when present because it preserves headers, footers, page
numbering, styles and embedded objects. When LibreOffice is not installed we
fall back to a pure-Python pipeline (python-docx / mammoth / PyMuPDF Story)
which keeps the document editable content intact but has reduced fidelity for
page furniture. The method used is always reported in the job metadata.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pymupdf

from ..errors import ConversionFailed, EngineUnavailable
from . import validation as v

log = logging.getLogger(__name__)

_ALLOWED_INPUTS = {".docx", ".doc", ".odt", ".rtf", ".txt", ".xlsx", ".pptx"}


def libreoffice_path() -> str | None:
    for candidate in ("soffice", "libreoffice"):
        path = shutil.which(candidate)
        if path:
            return path
    return None


def libreoffice_available() -> bool:
    return libreoffice_path() is not None


def convert_with_libreoffice(source: Path, outdir: Path, target: str, timeout: int = 180) -> Path:
    """Convert ``source`` to ``target`` (e.g. ``pdf``) in an isolated profile."""
    binary = libreoffice_path()
    if not binary:
        raise EngineUnavailable(
            "The LibreOffice renderer is not installed on this server.",
            code="libreoffice_unavailable",
        )
    if source.suffix.lower() not in _ALLOWED_INPUTS:
        raise ConversionFailed("This file type cannot be rendered by LibreOffice.")

    profile = Path(tempfile.mkdtemp(prefix="lo-profile-", dir=str(outdir)))
    outdir.mkdir(parents=True, exist_ok=True)
    command = [
        binary,
        "--headless",
        "--norestore",
        "--nolockcheck",
        "--nodefault",
        "--nofirststartwizard",
        "--nologo",
        f"-env:UserInstallation=file://{profile}",
        "--convert-to",
        target,
        "--outdir",
        str(outdir),
        str(source),
    ]
    env = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "HOME": str(profile),
        "LANG": "en_US.UTF-8",
        "LC_ALL": "en_US.UTF-8",
        "SAL_USE_VCLPLUGIN": "svp",
    }
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=env,
            cwd=str(outdir),
        )
    except subprocess.TimeoutExpired as exc:
        raise ConversionFailed("The document took too long to render. Try a smaller or simpler file.") from exc
    finally:
        shutil.rmtree(profile, ignore_errors=True)

    produced = outdir / f"{source.stem}.{target}"
    if not produced.exists():
        # LibreOffice may alter the extension casing; find the newest matching file.
        candidates = sorted(
            (p for p in outdir.iterdir() if p.suffix.lower() == f".{target.lower()}"),
            key=lambda p: p.stat().st_mtime,
        )
        if not candidates:
            log.warning("LibreOffice failed (exit %s): %s", result.returncode, result.stderr[-400:])
            raise ConversionFailed("LibreOffice could not render this document. It may use unsupported features.")
        produced = candidates[-1]
    if produced.stat().st_size == 0:
        raise ConversionFailed("LibreOffice produced an empty document.")
    return produced


def docx_to_pdf_fallback(source: Path, destination: Path, title: str | None = None) -> str:
    """Render a DOCX as PDF without LibreOffice, via HTML + PyMuPDF Story."""
    import mammoth

    try:
        with source.open("rb") as fh:
            result = mammoth.convert_to_html(fh)
        html = result.value
    except Exception as exc:
        raise ConversionFailed("This Word document could not be read.") from exc
    if not html.strip():
        raise ConversionFailed("This Word document contains no readable content.")

    css = """
    body { font-family: 'Liberation Sans', 'DejaVu Sans', sans-serif; font-size: 10.5pt;
           line-height: 1.45; color: #111827; }
    h1 { font-size: 20pt; margin: 0 0 10pt 0; color: #0f172a; }
    h2 { font-size: 15pt; margin: 14pt 0 7pt 0; color: #0f172a; }
    h3 { font-size: 12.5pt; margin: 12pt 0 6pt 0; }
    p { margin: 0 0 7pt 0; text-align: justify; }
    table { border-collapse: collapse; margin: 8pt 0; width: 100%; }
    td, th { border: 0.6pt solid #cbd5e1; padding: 4pt 6pt; vertical-align: top; }
    th { background: #f1f5f9; font-weight: bold; }
    img { max-width: 100%; }
    blockquote { margin: 8pt 18pt; color: #475569; }
    code { font-family: 'DejaVu Sans Mono', monospace; font-size: 9pt; }
    """
    if title:
        html = f"<h1>{_escape(title)}</h1>" + html
    story = pymupdf.Story(html=html, user_css=css)
    writer = pymupdf.DocumentWriter(str(destination))
    page_rect = pymupdf.paper_rect("a4")
    content_rect = page_rect + (56, 60, -56, -56)
    more = 1
    pages = 0
    try:
        while more:
            device = writer.begin_page(page_rect)
            more, _ = story.place(content_rect)
            story.draw(device)
            writer.end_page()
            pages += 1
            if pages > 2000:  # safety valve
                break
    finally:
        writer.close()
    v.validate_pdf(destination)
    return "html-fallback"


def _escape(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
