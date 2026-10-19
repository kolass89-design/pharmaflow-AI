"""Upload intake: streaming to disk, signature checks and cheap metadata."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pymupdf
from PIL import Image

from .config import Settings
from .engines.models import ConversionSpec
from .engines.registry import get_spec
from .errors import PayloadTooLarge, UnsupportedInput, ValidationError
from .jobs import UploadedSource
from .security import assert_upload_matches, sanitize_filename, split_extension

log = logging.getLogger(__name__)

CHUNK = 1024 * 256
IMAGE_KINDS = {"jpeg", "png", "webp", "heif", "gif", "bmp", "tiff"}


async def save_upload(upload, destination: Path, limit: int, running_total: list[int], job_limit: int) -> int:
    """Stream an UploadFile to disk, enforcing per-file and per-job limits."""
    size = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as fh:
        while True:
            chunk = await upload.read(CHUNK)
            if not chunk:
                break
            size += len(chunk)
            if size > limit:
                raise PayloadTooLarge(
                    f"“{upload.filename or 'file'}” exceeds the {limit // (1024 * 1024)} MB per-file limit.",
                    code="file_too_large",
                )
            running_total[0] += len(chunk)
            if running_total[0] > job_limit:
                raise PayloadTooLarge(
                    f"This upload exceeds the {job_limit // (1024 * 1024)} MB total limit.",
                    code="job_too_large",
                )
            fh.write(chunk)
    return size


def _pdf_pages(path: Path, settings: Settings) -> int:
    try:
        with pymupdf.open(path) as doc:
            if doc.needs_pass:
                return doc.page_count
            count = doc.page_count
    except Exception as exc:
        raise UnsupportedInput("This PDF could not be opened. It may be damaged.", code="invalid_file") from exc
    if count > settings.max_pages:
        raise ValidationError(
            f"This PDF has {count} pages; the limit is {settings.max_pages}.",
            code="too_many_pages",
        )
    return count


def _image_dimensions(path: Path, settings: Settings) -> tuple[int, int]:
    Image.MAX_IMAGE_PIXELS = settings.max_pixels
    try:
        with Image.open(path) as probe:
            width, height = probe.size
    except Image.DecompressionBombError as exc:
        raise ValidationError("The image is too large to process safely.", code="image_too_large") from exc
    except Exception as exc:
        raise UnsupportedInput("This image could not be read.", code="invalid_file") from exc
    if width <= 0 or height <= 0:
        raise UnsupportedInput("This image has invalid dimensions.", code="invalid_file")
    if width * height > settings.max_pixels:
        raise ValidationError("The image resolution exceeds the allowed limit.", code="image_too_large")
    return width, height


def validate_inputs(spec: ConversionSpec, saved: list[tuple[Path, str]], settings: Settings) -> list[UploadedSource]:
    """Validate already-saved uploads against the tool's declared input contract."""
    if len(saved) < spec.min_files:
        raise ValidationError(
            f"“{spec.title}” needs at least {spec.min_files} file{'s' if spec.min_files > 1 else ''}.",
            code="too_few_files",
        )
    if len(saved) > spec.max_files:
        raise ValidationError(
            f"“{spec.title}” accepts at most {spec.max_files} files per job.",
            code="too_many_files",
        )
    sources: list[UploadedSource] = []
    allowed = spec.input.extensions
    for path, original_name in saved:
        safe_name = sanitize_filename(original_name, fallback=f"file.{split_extension(original_name) or 'bin'}")
        kind = assert_upload_matches(path, safe_name, allowed, settings)
        pages = None
        if kind == "pdf":
            pages = _pdf_pages(path, settings)
        elif kind in IMAGE_KINDS:
            _image_dimensions(path, settings)
        sources.append(
            UploadedSource(
                path=path,
                original_name=original_name[:200] or safe_name,
                safe_name=safe_name,
                kind=kind,
                size=path.stat().st_size,
                pages=pages,
            )
        )
    return sources


def discard_staging(staging: Path) -> None:
    import shutil

    shutil.rmtree(staging, ignore_errors=True)


def describe_tool(tool: str) -> dict[str, Any]:
    spec = get_spec(tool)
    return spec.public() if spec else {}
