#!/usr/bin/env bash
# Create the Python environment used by the API, tests and verification scripts.
#
#   ./scripts/setup_env.sh            # core dependencies
#   ./scripts/setup_env.sh --ocr      # also install the pip-only OCR fallback
#
# Why a script instead of a plain pip call: rapidocr-onnxruntime depends on the
# full OpenCV wheel, which needs libGL. On a headless host that import fails with
# "libGL.so.1: cannot open shared object file". Installing the headless wheel
# afterwards is not enough, because both packages ship the same cv2 directory,
# so the script removes the full wheel and force-reinstalls the headless one.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv="${DOCUPRO_VENV:-$root/.venv}"
want_ocr=0
for arg in "$@"; do
  case "$arg" in
    --ocr) want_ocr=1 ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

if [ ! -x "$venv/bin/python" ]; then
  echo "creating $venv"
  python3 -m venv "$venv"
fi
"$venv/bin/pip" install --upgrade pip >/dev/null
"$venv/bin/pip" install -r "$root/services/api/requirements-dev.txt"

if [ "$want_ocr" = "1" ]; then
  "$venv/bin/pip" install -r "$root/services/api/requirements-ocr.txt"
  if "$venv/bin/pip" show opencv-python >/dev/null 2>&1; then
    echo "removing the full OpenCV wheel installed by rapidocr-onnxruntime"
    "$venv/bin/pip" uninstall -y opencv-python >/dev/null
    "$venv/bin/pip" install --force-reinstall --no-deps "opencv-python-headless==4.10.0.84"
  fi
fi

"$venv/bin/python" - <<'PY'
import importlib
missing = []
for name in ("fastapi", "uvicorn", "pymupdf", "docx", "PIL", "openpyxl", "pdf2docx"):
    try:
        importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - diagnostic only
        missing.append(f"{name}: {exc}")
if missing:
    raise SystemExit("environment incomplete:\n  " + "\n  ".join(missing))
try:
    import cv2  # noqa: F401
    from rapidocr_onnxruntime import RapidOCR  # noqa: F401
    print("imports ok (OCR fallback available)")
except Exception:
    print("imports ok (OCR fallback not installed; install Tesseract or run with --ocr)")
PY
echo "ready: $venv"
