#!/usr/bin/env python3
"""Render the PNG and JPEG exports for every wallpaper from its SVG.

The SVG in each variant folder is the source of truth. This renders it at every
target width for its platform, writes <stem>-<width>x<height>.png and .jpg next
to it, and removes exports that no longer belong.

Needs rsvg-convert (librsvg) and Pillow.
"""

import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WALLPAPERS = REPO / "wallpapers"

# Widths rendered per platform. Heights follow from the SVG's own aspect ratio,
# so a portrait mobile design stays portrait.
TARGET_WIDTHS = {
    "desktop": (3840, 2560, 1920),
    "mobile": (1290, 1080),
}

JPEG_QUALITY = 90
VIEWBOX = re.compile(r"[\s,]+")


def aspect_of(svg):
    """Return (width, height) in user units from the viewBox, or None."""
    try:
        root = ET.parse(svg).getroot()
    except ET.ParseError:
        return None

    box = root.get("viewBox")
    if box:
        parts = VIEWBOX.split(box.strip())
        if len(parts) == 4:
            try:
                width, height = float(parts[2]), float(parts[3])
            except ValueError:
                return None
            if width > 0 and height > 0:
                return width, height

    # Fall back to plain width/height attributes when they carry real numbers.
    try:
        width = float(re.sub(r"[a-z%]+$", "", (root.get("width") or "").strip()))
        height = float(re.sub(r"[a-z%]+$", "", (root.get("height") or "").strip()))
    except ValueError:
        return None
    return (width, height) if width > 0 and height > 0 else None


def render_png(svg, width, height, destination):
    subprocess.run(
        [
            "rsvg-convert",
            "--width", str(width),
            "--height", str(height),
            "--format", "png",
            "--output", str(destination),
            str(svg),
        ],
        check=True,
        capture_output=True,
    )


def write_jpeg(png, destination):
    from PIL import Image

    with Image.open(png) as image:
        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGBA")
            flat = Image.new("RGB", image.size, (255, 255, 255))
            flat.paste(image, mask=image.split()[-1])
            image = flat
        else:
            image = image.convert("RGB")
        image.save(
            destination,
            "JPEG",
            quality=JPEG_QUALITY,
            optimize=True,
            progressive=True,
            subsampling=0,
        )


def render_variant(svg, widths, written, removed):
    folder = svg.parent
    aspect = aspect_of(svg)
    if aspect is None:
        raise SystemExit(f"{svg.relative_to(REPO)}: no usable viewBox or size, cannot render")

    view_width, view_height = aspect
    expected = set()

    for width in widths:
        height = round(width * view_height / view_width)
        png = folder / f"{svg.stem}-{width}x{height}.png"
        jpeg = folder / f"{svg.stem}-{width}x{height}.jpg"
        expected.update({png.name, jpeg.name})

        render_png(svg, width, height, png)
        write_jpeg(png, jpeg)
        written.extend([png, jpeg])

    for raster in folder.iterdir():
        if raster.suffix in (".png", ".jpg") and raster.name not in expected:
            raster.unlink()
            removed.append(raster)


def main():
    if shutil.which("rsvg-convert") is None:
        raise SystemExit(
            "rsvg-convert is missing. Install librsvg: brew install librsvg, "
            "or apt-get install librsvg2-bin."
        )

    written, removed, sources = [], [], 0
    for platform, widths in TARGET_WIDTHS.items():
        platform_dir = WALLPAPERS / platform
        if not platform_dir.is_dir():
            continue
        for svg in sorted(platform_dir.rglob("*.svg")):
            sources += 1
            render_variant(svg, widths, written, removed)

    for path in removed:
        print(f"removed {path.relative_to(REPO)}")
    print(f"Rendered {len(written)} export(s) from {sources} SVG(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
