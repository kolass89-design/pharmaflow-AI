"""Generate every DOCUPRO icon from one vector definition.

Usage: python scripts/make_icons.py

Writes:
  apps/web/public/icons/{icon-192,icon-512,maskable-512,apple-touch-icon}.png
  apps/web/public/favicon.svg
  apps/desktop/src-tauri/icons/{32x32,128x128,128x128@2x,icon,Square*Logo}.png
  apps/desktop/src-tauri/icons/icon.ico
  apps/desktop/src-tauri/icons/icon.icns
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "apps" / "web" / "public"
TAURI = ROOT / "apps" / "desktop" / "src-tauri" / "icons"

INK = (15, 23, 42)
SHEET = (255, 255, 255)
ACCENT = (37, 99, 235)
SOFT = (147, 197, 253)


def _rounded_mask(size: int, radius_ratio: float) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * radius_ratio), fill=255)
    return mask


def render(size: int, *, maskable: bool = False, transparent: bool = False) -> Image.Image:
    scale = 4
    s = size * scale
    canvas = Image.new("RGBA", (s, s), (0, 0, 0, 0))

    # Diagonal brand gradient.
    gradient = Image.new("RGB", (s, s))
    pixels = gradient.load()
    for y in range(s):
        for x in range(0, s, 2):
            t = (x / s + y / s) / 2
            r = int(37 + (14 - 37) * t)
            g = int(99 + (116 - 99) * t)
            b = int(235 + (144 - 235) * t)
            pixels[x, y] = (r, g, b)
            if x + 1 < s:
                pixels[x + 1, y] = (r, g, b)

    if not transparent:
        radius = 0.5 if maskable else 0.235
        canvas.paste(gradient, (0, 0), _rounded_mask(s, radius))
    else:
        canvas.paste(gradient, (0, 0))

    draw = ImageDraw.Draw(canvas)
    inset = 0.30 if maskable else 0.24
    width = s * (1 - 2 * inset)
    height = width * 1.28
    left = (s - width) / 2
    top = (s - height) / 2
    fold = width * 0.30
    radius = width * 0.08

    # Sheet with a folded corner.
    draw.rounded_rectangle([left, top, left + width, top + height], radius=radius, fill=SHEET)
    draw.polygon(
        [(left + width - fold, top), (left + width, top + fold), (left + width - fold, top + fold)],
        fill=(191, 219, 254),
    )
    draw.line(
        [(left + width - fold, top), (left + width - fold, top + fold), (left + width, top + fold)],
        fill=(96, 165, 250),
        width=max(2, int(width * 0.018)),
    )

    # Conversion arrow and text lines.
    line_w = max(3, int(width * 0.085))
    mid = top + height * 0.44
    x0, x1 = left + width * 0.22, left + width * 0.74
    draw.line([(x0, mid), (x1, mid)], fill=ACCENT, width=line_w)
    head = width * 0.16
    draw.line([(x1 - head, mid - head), (x1, mid), (x1 - head, mid + head)], fill=ACCENT, width=line_w, joint="curve")
    for i, factor in enumerate((0.62, 0.74)):
        y = mid + height * 0.14 * (i + 1)
        draw.line([(left + width * 0.22, y), (left + width * factor, y)], fill=SOFT, width=line_w)
    return canvas.resize((size, size), Image.LANCZOS)


def favicon_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="DOCUPRO">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#2563eb"/><stop offset="1" stop-color="#0e7490"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="15" fill="url(#g)"/>
  <path d="M23 13h13.5L46 22.5V43a4 4 0 0 1-4 4H23a4 4 0 0 1-4-4V17a4 4 0 0 1 4-4Z" fill="#fff"/>
  <path d="M36.5 13 46 22.5h-6.5a3 3 0 0 1-3-3V13Z" fill="#bfdbfe"/>
  <path d="M27 30.5h11m0 0-4-4m4 4-4 4" stroke="#2563eb" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M27 38h9" stroke="#93c5fd" stroke-width="2.6" stroke-linecap="round"/>
</svg>
"""


def main() -> int:
    (WEB / "icons").mkdir(parents=True, exist_ok=True)
    TAURI.mkdir(parents=True, exist_ok=True)

    for name, size in (("icon-192.png", 192), ("icon-512.png", 512), ("apple-touch-icon.png", 180)):
        render(size).save(WEB / "icons" / name, optimize=True)
    render(512, maskable=True).save(WEB / "icons" / "maskable-512.png", optimize=True)
    (WEB / "favicon.svg").write_text(favicon_svg(), encoding="utf-8")

    render(32).save(TAURI / "32x32.png")
    render(128).save(TAURI / "128x128.png")
    render(256).save(TAURI / "128x128@2x.png")
    render(512).save(TAURI / "icon.png")
    square_logos = {
        "Square30x30Logo.png": 30,
        "Square44x44Logo.png": 44,
        "Square71x71Logo.png": 71,
        "Square89x89Logo.png": 89,
        "Square107x107Logo.png": 107,
        "Square142x142Logo.png": 142,
        "Square150x150Logo.png": 150,
        "Square284x284Logo.png": 284,
        "Square310x310Logo.png": 310,
        "StoreLogo.png": 50,
    }
    for name, size in square_logos.items():
        render(size).save(TAURI / name)

    ico = [render(s) for s in (16, 24, 32, 48, 64, 128, 256)]
    ico[0].save(TAURI / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    try:
        render(512).save(TAURI / "icon.icns")
    except Exception as exc:  # pragma: no cover - Pillow without ICNS support
        print(f"warning: could not write icns ({exc})")

    print("icons written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
