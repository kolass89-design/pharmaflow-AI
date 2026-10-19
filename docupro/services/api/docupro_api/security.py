"""Upload validation, abuse protection and safe naming.

The rules here are deliberately conservative: a file must both declare an
extension we accept for the requested conversion *and* have a matching
magic-number signature. A renamed executable, a zip bomb masquerading as a
DOCX, or a path-traversal filename is rejected before any parser sees it.
"""

from __future__ import annotations

import io
import re
import threading
import time
import unicodedata
import zipfile
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import quote

from .config import Settings
from .errors import UnsupportedInput, ValidationError

# --- magic number detection -------------------------------------------------

_JPEG = b"\xff\xd8\xff"
_PNG = b"\x89PNG\r\n\x1a\n"
_GIF = (b"GIF87a", b"GIF89a")
_BMP = b"BM"
_TIFF = (b"II*\x00", b"MM\x00*")
_OLE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
_ZIP = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
_HEIF_BRANDS = {
    b"heic",
    b"heix",
    b"hevc",
    b"hevx",
    b"heim",
    b"heis",
    b"hevm",
    b"hevs",
    b"mif1",
    b"msf1",
    b"avif",
    b"avis",
}

#: extension -> set of acceptable detected "kinds"
EXTENSION_KINDS: dict[str, set[str]] = {
    "pdf": {"pdf"},
    "docx": {"docx"},
    "doc": {"doc"},
    "xlsx": {"xlsx"},
    "xls": {"xls"},
    "pptx": {"pptx"},
    "csv": {"text"},
    "txt": {"text"},
    "html": {"text"},
    "htm": {"text"},
    "md": {"text"},
    "jpg": {"jpeg"},
    "jpeg": {"jpeg"},
    "png": {"png"},
    "webp": {"webp"},
    "heic": {"heif"},
    "heif": {"heif"},
    "gif": {"gif"},
    "bmp": {"bmp"},
    "tif": {"tiff"},
    "tiff": {"tiff"},
}

IMAGE_KINDS = {"jpeg", "png", "webp", "heif", "gif", "bmp", "tiff"}


def detect_kind(path: Path) -> str:
    """Return a coarse content kind derived from the file's leading bytes."""
    with path.open("rb") as fh:
        head = fh.read(4096)

    if not head:
        return "empty"
    if head.startswith(b"%PDF-"):
        return "pdf"
    if head.startswith(_JPEG):
        return "jpeg"
    if head.startswith(_PNG):
        return "png"
    if head.startswith(_GIF):
        return "gif"
    if head.startswith(_BMP):
        return "bmp"
    if head.startswith(_TIFF):
        return "tiff"
    if head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return "webp"
    if len(head) >= 12 and head[4:8] == b"ftyp":
        if head[8:12] in _HEIF_BRANDS:
            return "heif"
    if head.startswith(_OLE):
        return "ole"
    if head.startswith(_ZIP) or head[:2] == b"PK":
        return _detect_ooxml(path)
    if b"\x00" in head[:2048]:
        return "binary"
    try:
        head.decode("utf-8")
    except UnicodeDecodeError:
        try:
            head.decode("cp1252")
        except UnicodeDecodeError:
            return "binary"
    return "text"


def _detect_ooxml(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
    except (zipfile.BadZipFile, OSError):
        return "binary"
    if any(n.startswith("word/") for n in names):
        return "docx"
    if any(n.startswith("xl/") for n in names):
        return "xlsx"
    if any(n.startswith("ppt/") for n in names):
        return "pptx"
    return "zip"


def assert_ooxml_safe(path: Path, settings: Settings) -> None:
    """Reject zip bombs and suspiciously structured OOXML packages."""
    try:
        with zipfile.ZipFile(path) as zf:
            infos = zf.infolist()
    except (zipfile.BadZipFile, OSError) as exc:
        raise UnsupportedInput("The Office file is corrupt or not a valid OOXML package.") from exc

    if len(infos) > settings.max_ooxml_entries:
        raise UnsupportedInput(
            "The Office file contains an unreasonable number of internal parts.",
            details={"reason": "compression_bomb"},
        )
    total = sum(info.file_size for info in infos)
    if total > settings.max_ooxml_uncompressed:
        raise UnsupportedInput(
            "The Office file expands beyond the allowed size; it may be a compression bomb.",
            details={"reason": "compression_bomb"},
        )
    for info in infos:
        name = info.filename
        if name.startswith("/") or ".." in Path(name).parts:
            raise UnsupportedInput("The Office file contains an unsafe internal path.")


# --- filename handling ------------------------------------------------------

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_UNSAFE_PATH = re.compile(r"[\\/]+")
_WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize_filename(name: str, *, fallback: str = "document", max_length: int = 120) -> str:
    """Produce a safe, human readable file name (no path components)."""
    name = unicodedata.normalize("NFKC", name or "")
    name = _UNSAFE_PATH.sub("_", name)
    name = _CONTROL_CHARS.sub("", name).strip().strip(".")
    name = re.sub(r"\.{2,}", ".", name)
    name = re.sub(r"\s+", " ", name)
    if not name:
        return fallback
    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, ""
    if stem.upper() in _WINDOWS_RESERVED:
        stem = f"_{stem}"
    stem = stem[: max_length - len(ext) - 1].strip() or fallback
    return f"{stem}.{ext}" if ext else stem


def split_extension(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


def assert_upload_matches(path: Path, filename: str, allowed_exts: Iterable[str], settings: Settings) -> str:
    """Validate an uploaded file against the conversions accepted inputs.

    Returns the detected content kind. Raises :class:`UnsupportedInput`.
    """
    ext = split_extension(filename)
    allowed = set(allowed_exts)
    if ext not in allowed:
        raise UnsupportedInput(
            f"Files of type .{ext or '?'} are not accepted for this conversion.",
            code="unsupported_input",
            details={"allowed_extensions": sorted(allowed)},
        )
    if path.stat().st_size == 0:
        raise ValidationError("The uploaded file is empty.", code="invalid_file")
    if path.stat().st_size > settings.max_upload_bytes:
        raise ValidationError(
            f"The file exceeds the {settings.max_upload_bytes // (1024 * 1024)} MB limit.",
            code="file_too_large",
        )

    kind = detect_kind(path)
    expected = EXTENSION_KINDS.get(ext, set())
    if "doc" in expected and kind == "ole":
        kind = "doc"
    if kind == "ole" and ext in {"xls", "doc"}:
        kind = ext
    if kind not in expected:
        raise UnsupportedInput(
            "The file content does not match its extension and was rejected.",
            code="invalid_file",
            details={"extension": ext},
        )
    if kind in {"docx", "xlsx", "pptx"}:
        assert_ooxml_safe(path, settings)
    return kind


# --- rate limiting ----------------------------------------------------------


class RateLimiter:
    """Thread-safe token bucket keyed by client identity."""

    def __init__(self, rate_per_minute: int, burst: int) -> None:
        self.rate = max(1, rate_per_minute) / 60.0
        self.burst = max(1, burst)
        self._buckets: dict[str, tuple[float, float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds)."""
        now = time.monotonic()
        with self._lock:
            tokens, last = self._buckets.get(key, (float(self.burst), now))
            tokens = min(float(self.burst), tokens + (now - last) * self.rate)
            if tokens < 1.0:
                retry = int((1.0 - tokens) / self.rate) + 1
                self._buckets[key] = (tokens, now)
                return False, retry
            self._buckets[key] = (tokens - 1.0, now)
            if len(self._buckets) > 20_000:  # bound memory under abuse
                cutoff = now - 600
                self._buckets = {k: v for k, v in self._buckets.items() if v[1] >= cutoff}
            return True, 0


def client_identity(headers: dict[str, str], peer: str | None, trust_proxy: bool) -> str:
    """Best-effort client identity for rate limiting."""
    if trust_proxy:
        forwarded = headers.get("x-forwarded-for") or headers.get("cf-connecting-ip")
        if forwarded:
            return forwarded.split(",")[0].strip()[:64]
    return (peer or "unknown")[:64]


# --- output handling -------------------------------------------------------


def content_disposition(filename: str) -> str:
    """RFC 6266/5987 compliant header value that survives Unicode names."""
    safe = sanitize_filename(filename)
    transliterated = unicodedata.normalize("NFKD", safe).encode("ascii", "ignore").decode("ascii")
    transliterated = re.sub(r"[^A-Za-z0-9 ._-]", "_", transliterated).strip() or "download"
    encoded = quote(safe, safe="-._~")
    return f"attachment; filename=\"{transliterated}\"; filename*=UTF-8''{encoded}"


def guard_zip_bytes(data: bytes, max_entries: int = 5000) -> None:
    """Defensive check for archives we build ourselves."""
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        if len(zf.infolist()) > max_entries:
            raise ValidationError("Archive contains too many files.")
