#!/usr/bin/env python3
"""Download a license-friendly tools icon and replace rigX Utility Tools icon.

This script fetches Google's Material Design "build" (wrench) PNG
under Apache-2.0, composites it on the rigX green gradient background,
and saves to config/icons/rigX_icon_utils.png (64x64).
"""

from __future__ import annotations

import io
import os
import sys
import urllib.request
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except Exception as import_error:  # pragma: no cover
    raise SystemExit(
        "Pillow (PIL) is required. Install with: python -m pip install --user pillow\n"
        f"Original import error: {import_error}"
    )


# OpenMoji hammer and wrench (U+1F6E0) PNG, CC BY-SA 4.0
# See https://openmoji.org for licensing and attribution requirements.
RAW_ICON_URL = (
    "https://cdn.jsdelivr.net/gh/hfg-gmuend/openmoji@14.0.0/color/72x72/1F6E0.png"
)


def _draw_vertical_gradient(bg_img: Image.Image, top_color: tuple[int, int, int, int], bottom_color: tuple[int, int, int, int]) -> None:
    width, height = bg_img.size
    draw_bg = ImageDraw.Draw(bg_img)
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
        g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
        b = int(top_color[2] * (1 - t) + bottom_color[2] * t)
        a = int(top_color[3] * (1 - t) + bottom_color[3] * t)
        draw_bg.line([(0, y), (width, y)], fill=(r, g, b, a))


def _rounded_paste(base: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", base.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([1, 1, base.width - 2, base.height - 2], radius=max(2, radius), fill=255)
    out = Image.new("RGBA", base.size, (0, 0, 0, 0))
    out.paste(base, (0, 0), mask)
    return out


def download_icon(url: str) -> Image.Image:
    with urllib.request.urlopen(url) as resp:
        data = resp.read()
    return Image.open(io.BytesIO(data)).convert("RGBA")


def to_white_silhouette(img: Image.Image) -> Image.Image:
    """Return a pure white silhouette using the source alpha as mask."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    # Extract alpha channel as mask
    alpha = img.split()[3]
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(white, (0, 0), alpha)
    return out


def composite_icon(glyph: Image.Image, size: int = 64) -> Image.Image:
    # Create background gradient (rigX brand green)
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    _draw_vertical_gradient(bg, (27, 67, 50, 255), (64, 145, 108, 255))
    bg = _rounded_paste(bg, 8)

    # Resize glyph to fit with padding
    # Smaller padding to make the glyph appear larger on the button
    pad = int(round(size * 0.12))
    max_w = size - 2 * pad
    max_h = size - 2 * pad
    scale = min(max_w / glyph.width, max_h / glyph.height)
    new_w = max(1, int(round(glyph.width * scale)))
    new_h = max(1, int(round(glyph.height * scale)))
    glyph_resized = glyph.resize((new_w, new_h), Image.LANCZOS)

    # Center paste
    x = (size - new_w) // 2
    y = (size - new_h) // 2
    bg.paste(glyph_resized, (x, y), glyph_resized)
    return bg


def main() -> int:
    repo_root = Path(__file__).parent.parent
    out_path = repo_root / "config" / "icons" / "rigX_icon_utils.png"

    try:
        print("Downloading tools glyph...")
        glyph = download_icon(RAW_ICON_URL)
        glyph = to_white_silhouette(glyph)
        print("Compositing onto brand background...")
        icon = composite_icon(glyph, 64)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        icon.save(out_path, "PNG")
        print(f"Saved: {out_path}")
        return 0
    except Exception as exc:
        print(f"Failed to replace Tools icon: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())


