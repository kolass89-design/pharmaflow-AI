"""OCR with pluggable backends.

Tesseract is the preferred engine (wide language coverage, no model download).
A pure-Python ONNX fallback (RapidOCR) keeps OCR functional on hosts where
Tesseract cannot be installed. Both return line-level boxes so we can rebuild
paragraphs and stamp an invisible text layer into searchable PDFs.
"""

from __future__ import annotations

import functools
import logging
import re
import shutil
from collections.abc import Iterable
from dataclasses import dataclass

from PIL import Image, ImageOps

from ..errors import EngineUnavailable, ValidationError

log = logging.getLogger(__name__)

#: Friendly language choices -> Tesseract codes. Mirrors the UI selector.
LANGUAGE_CHOICES: tuple[tuple[str, str], ...] = (
    ("auto", "Automatic (English + French)"),
    ("eng", "English"),
    ("fra", "French"),
    ("eng+fra", "English + French"),
    ("spa", "Spanish"),
    ("deu", "German"),
    ("ita", "Italian"),
    ("por", "Portuguese"),
    ("nld", "Dutch"),
    ("ara", "Arabic"),
    ("rus", "Russian"),
    ("hin", "Hindi"),
    ("chi_sim", "Chinese (Simplified)"),
)

_TESSERACT_READY: bool | None = None
_RAPID_ENGINE = None
_RAPID_FAILED = False


@dataclass
class OcrLine:
    text: str
    bbox: tuple[float, float, float, float]
    confidence: float = 0.0

    @property
    def top(self) -> float:
        return self.bbox[1]

    @property
    def bottom(self) -> float:
        return self.bbox[3]

    @property
    def height(self) -> float:
        return max(1.0, self.bbox[3] - self.bbox[1])


def _normalise_lang(lang: str | None) -> str:
    code = (lang or "auto").strip().lower()
    if not re.fullmatch(r"[a-z_+]{2,40}", code):
        raise ValidationError("Unsupported OCR language selection.", code="invalid_language")
    return code


def tesseract_available() -> bool:
    global _TESSERACT_READY
    if _TESSERACT_READY is None:
        _TESSERACT_READY = shutil.which("tesseract") is not None
    return _TESSERACT_READY


@functools.lru_cache(maxsize=1)
def tesseract_languages() -> tuple[str, ...]:
    if not tesseract_available():
        return ()
    try:
        import pytesseract

        langs = pytesseract.get_languages(config="")
        return tuple(sorted(code for code in langs if code and code != "osd"))
    except Exception:  # pragma: no cover - defensive
        return ("eng",)


@functools.lru_cache(maxsize=1)
def _rapid_engine():
    global _RAPID_ENGINE, _RAPID_FAILED
    if _RAPID_ENGINE is not None or _RAPID_FAILED:
        return _RAPID_ENGINE
    try:
        from rapidocr_onnxruntime import RapidOCR

        _RAPID_ENGINE = RapidOCR()
    except Exception as exc:  # pragma: no cover - optional dependency
        log.info("RapidOCR backend unavailable: %s", exc)
        _RAPID_FAILED = True
        _RAPID_ENGINE = None
    return _RAPID_ENGINE


def ocr_backend() -> str | None:
    if tesseract_available():
        return "tesseract"
    if _rapid_engine() is not None:
        return "rapidocr"
    return None


def require_ocr_engine() -> str:
    backend = ocr_backend()
    if backend is None:
        raise EngineUnavailable(
            "OCR is not available on this server. Install Tesseract or enable the OCR fallback engine.",
            code="ocr_unavailable",
        )
    return backend


def available_languages() -> list[dict[str, str]]:
    """Languages that can actually be used by the active backend."""
    backend = ocr_backend()
    if backend == "tesseract":
        installed = set(tesseract_languages())
        result = []
        for code, label in LANGUAGE_CHOICES:
            if code == "auto":
                result.append({"value": code, "label": label})
            elif "+" in code:
                required = code.split("+")
                if all(code in installed for code in required):
                    result.append({"value": code, "label": label})
            elif code in installed:
                result.append({"value": code, "label": label})
        if not any(r["value"] != "auto" for r in result):
            result.append({"value": "eng", "label": "English"})
        return result
    if backend == "rapidocr":
        # ONNX models handle Latin/CJK scripts but do not take a language code.
        return [{"value": "auto", "label": "Automatic (Latin script)"}]
    return []


def _resolve_tesseract_lang(lang: str) -> str:
    installed = set(tesseract_languages()) or {"eng"}
    if lang == "auto":
        preferred = [c for c in ("eng", "fra") if c in installed]
        return "+".join(preferred) or next(iter(installed))
    parts = lang.split("+")
    missing = [p for p in parts if p not in installed]
    if missing:
        raise ValidationError(
            "The selected OCR language is not installed on this server.",
            code="invalid_language",
            details={"missing": missing, "installed": sorted(installed)},
        )
    return lang


def _prepare(img: Image.Image, *, upscale: bool = True) -> Image.Image:
    """Normalise an image for OCR: grayscale, white background, sensible DPI."""
    if img.mode in {"RGBA", "LA", "P"}:
        rgba = img.convert("RGBA")
        canvas = Image.new("RGB", rgba.size, (255, 255, 255))
        canvas.paste(rgba, mask=rgba.split()[-1])
        img = canvas
    elif img.mode not in {"RGB", "L"}:
        img = img.convert("RGB")
    if upscale:
        shortest = min(img.size)
        if shortest < 900:
            factor = min(3.0, 900 / max(1, shortest))
            if factor > 1.05:
                img = img.resize((int(img.width * factor), int(img.height * factor)), Image.LANCZOS)
    return ImageOps.autocontrast(img.convert("L"), cutoff=1)


def ocr_lines(img: Image.Image, lang: str = "auto") -> list[OcrLine]:
    """Run OCR and return lines sorted top-to-bottom, left-to-right."""
    backend = require_ocr_engine()
    code = _normalise_lang(lang)
    prepared = _prepare(img)
    if backend == "tesseract":
        return _tesseract_lines(prepared, _resolve_tesseract_lang(code))
    return _rapid_lines(prepared)


def _tesseract_lines(img: Image.Image, lang: str) -> list[OcrLine]:
    import pytesseract
    from pytesseract import Output

    try:
        data = pytesseract.image_to_data(img, lang=lang, config="--oem 1 --psm 3", output_type=Output.DICT)
    except pytesseract.TesseractError as exc:
        log.warning("Tesseract failed: %s", exc)
        raise EngineUnavailable("The OCR engine could not process this image.", code="ocr_failed") from exc

    grouped: dict[tuple[int, int, int], list[int]] = {}
    count = len(data.get("text", []))
    for i in range(count):
        word = (data["text"][i] or "").strip()
        if not word:
            continue
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            conf = 0.0
        if conf < 0:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        grouped.setdefault(key, []).append(i)

    lines: list[OcrLine] = []
    for indexes in grouped.values():
        words = [(data["text"][i] or "").strip() for i in indexes]
        text = " ".join(w for w in words if w)
        if not text:
            continue
        left = min(data["left"][i] for i in indexes)
        top = min(data["top"][i] for i in indexes)
        right = max(data["left"][i] + data["width"][i] for i in indexes)
        bottom = max(data["top"][i] + data["height"][i] for i in indexes)
        confs = []
        for i in indexes:
            try:
                confs.append(float(data["conf"][i]))
            except (TypeError, ValueError):
                pass
        confidence = sum(confs) / len(confs) / 100.0 if confs else 0.0
        lines.append(
            OcrLine(text=text, bbox=(float(left), float(top), float(right), float(bottom)), confidence=confidence)
        )
    lines.sort(key=lambda item: (round(item.top / 4), item.bbox[0]))
    return lines


def _rapid_lines(img: Image.Image) -> list[OcrLine]:
    engine = _rapid_engine()
    if engine is None:  # pragma: no cover - guarded by require_ocr_engine
        raise EngineUnavailable("OCR is not available on this server.", code="ocr_unavailable")
    import numpy as np

    result, _ = engine(np.array(img))
    if not result:
        return []
    lines: list[OcrLine] = []
    for item in result:
        box, text, score = item[0], item[1], float(item[2])
        xs = [float(point[0]) for point in box]
        ys = [float(point[1]) for point in box]
        if not (text or "").strip():
            continue
        lines.append(
            OcrLine(
                text=str(text).strip(),
                bbox=(min(xs), min(ys), max(xs), max(ys)),
                confidence=score,
            )
        )
    lines.sort(key=lambda item: (round(item.top / 6), item.bbox[0]))
    return lines


_HYPHEN_END = re.compile(r"[A-Za-zÀ-ÿ]-$")


def lines_to_paragraphs(lines: Iterable[OcrLine]) -> list[str]:
    """Rebuild paragraphs from OCR lines using vertical spacing heuristics."""
    ordered = list(lines)
    if not ordered:
        return []
    heights = sorted(item.height for item in ordered) or [10.0]
    median_h = heights[len(heights) // 2] or 10.0
    paragraphs: list[str] = []
    current: str = ""
    previous: OcrLine | None = None
    for line in ordered:
        text = re.sub(r"\s+", " ", line.text).strip()
        if not text:
            continue
        if previous is not None:
            gap = line.top - previous.bottom
            same_block = gap < median_h * 0.9
            starts_lower = text[0].islower()
            if current and same_block and (starts_lower or _HYPHEN_END.search(current)):
                if _HYPHEN_END.search(current):
                    current = current[:-1]
                else:
                    current += " "
                current += text
                previous = line
                continue
            if current:
                paragraphs.append(current)
            current = text
        else:
            current = text
        previous = line
    if current:
        paragraphs.append(current)
    return paragraphs


def ocr_to_text(img: Image.Image, lang: str = "auto") -> str:
    return "\n\n".join(lines_to_paragraphs(ocr_lines(img, lang)))


def check_pdf_page_text(page) -> bool:
    try:
        return bool(page.get_text("text").strip())
    except Exception:  # pragma: no cover - defensive
        return False


def looks_scanned(page) -> bool:
    """A page is 'scanned' when it has no text but does have images."""
    try:
        if page.get_text("text").strip():
            return False
        return bool(page.get_images(full=True))
    except Exception:  # pragma: no cover - defensive
        return False
