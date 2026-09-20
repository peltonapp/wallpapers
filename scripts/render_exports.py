#!/usr/bin/env python3
"""Render the PNG and JPEG exports for every wallpaper from its master file.

Each variant folder holds exactly one master, either a vector one:

    night-1-default.svg

or a raster one, for hand-drawn art and photography:

    night-1-default-master.png

This renders that master at every target width for its platform, writes
<stem>-<width>x<height>.png and .jpg next to it, and removes exports that no
longer belong. A raster master is never upscaled, so it only produces the
targets it is big enough for.

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

# A raster master is marked by this suffix so it is never mistaken for an export.
MASTER_SUFFIX = "-master"
RASTER_MASTERS = (".png", ".jpg")


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
    if shutil.which("rsvg-convert") is None:
        raise SystemExit(
            f"{svg.relative_to(REPO)} needs rsvg-convert, which is missing. "
            "Install librsvg: brew install librsvg, or apt-get install librsvg2-bin."
        )
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


def find_master(folder):
    """Return the variant's master file, vector or raster, or None."""
    svgs = sorted(folder.glob("*.svg"))
    if svgs:
        return svgs[0]
    rasters = sorted(
        path
        for path in folder.iterdir()
        if path.suffix in RASTER_MASTERS and path.stem.endswith(MASTER_SUFFIX)
    )
    return rasters[0] if rasters else None


def resize_png(master, width, height, destination):
    from PIL import Image

    with Image.open(master) as image:
        image.convert("RGBA" if image.mode in ("RGBA", "LA", "P") else "RGB").resize(
            (width, height), Image.Resampling.LANCZOS
        ).save(destination, "PNG", optimize=True)


def render_variant(master, widths, written, removed, skipped):
    folder = master.parent
    is_vector = master.suffix == ".svg"
    # The export stem drops the -master marker, so both kinds of master produce
    # identically named exports.
    stem = master.stem[: -len(MASTER_SUFFIX)] if not is_vector else master.stem

    if is_vector:
        size = aspect_of(master)
        if size is None:
            raise SystemExit(
                f"{master.relative_to(REPO)}: no usable viewBox or size, cannot render"
            )
    else:
        from PIL import Image

        with Image.open(master) as image:
            size = image.size

    source_width, source_height = size
    expected = {master.name}

    for width in widths:
        # Never upscale a raster master: that invents detail that is not there.
        if not is_vector and width > source_width:
            skipped.append((master, width))
            continue

        height = round(width * source_height / source_width)
        png = folder / f"{stem}-{width}x{height}.png"
        jpeg = folder / f"{stem}-{width}x{height}.jpg"
        expected.update({png.name, jpeg.name})

        if is_vector:
            render_png(master, width, height, png)
        else:
            resize_png(master, width, height, png)
        write_jpeg(png, jpeg)
        written.extend([png, jpeg])

    for raster in folder.iterdir():
        if raster.suffix in (".png", ".jpg") and raster.name not in expected:
            raster.unlink()
            removed.append(raster)


def main():
    written, removed, skipped, sources = [], [], [], 0
    for platform, widths in TARGET_WIDTHS.items():
        platform_dir = WALLPAPERS / platform
        if not platform_dir.is_dir():
            continue
        for folder in sorted(platform_dir.rglob("*")):
            if not folder.is_dir():
                continue
            master = find_master(folder)
            if master is None:
                continue
            sources += 1
            render_variant(master, widths, written, removed, skipped)

    for path in removed:
        print(f"removed {path.relative_to(REPO)}")
    for master, width in skipped:
        print(f"skipped {width}px for {master.relative_to(REPO)}, the master is smaller")
    print(f"Rendered {len(written)} export(s) from {sources} master(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
