#!/usr/bin/env python3
"""Check that wallpapers/ follows the layout and naming rules in CONTRIBUTING.md.

The SVG is the source of truth: every variant folder needs exactly one, and the
PNG and JPEG exports are rendered from it by scripts/render_exports.py. Exports
are optional here, since CI produces them, but any that exist have to be named
correctly and match their real pixel size.
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WALLPAPERS = REPO / "wallpapers"
PLATFORMS = ("desktop", "mobile")
DEPTH = 3  # <set>/<number>/<variant> below the platform folder

NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NUMBER = re.compile(r"^\d+$")
SIZED = re.compile(r"^(?P<stem>.+)-(?P<width>\d{3,5})x(?P<height>\d{3,5})$")
IGNORED = {".gitkeep", ".DS_Store"}


def png_size(path):
    import struct

    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", header[16:24])


def jpeg_size(path):
    """Walk JPEG segments to the frame header holding the real dimensions."""
    with path.open("rb") as handle:
        if handle.read(2) != b"\xff\xd8":
            return None
        while True:
            marker = handle.read(2)
            if len(marker) < 2 or marker[0] != 0xFF:
                return None
            length = int.from_bytes(handle.read(2), "big")
            if 0xC0 <= marker[1] <= 0xCF and marker[1] not in (0xC4, 0xC8, 0xCC):
                handle.read(1)
                height = int.from_bytes(handle.read(2), "big")
                width = int.from_bytes(handle.read(2), "big")
                return width, height
            handle.seek(length - 2, 1)


def image_size(path):
    try:
        return png_size(path) if path.suffix == ".png" else jpeg_size(path)
    except (OSError, ValueError):
        return None


def expected_stem(variant_dir, platform_dir):
    """A file in desktop/night/1/no-marker is named night-1-no-marker."""
    return "-".join(variant_dir.relative_to(platform_dir).parts)


def check_variant(variant_dir, platform_dir, problems):
    rel = variant_dir.relative_to(REPO).as_posix()
    stem = expected_stem(variant_dir, platform_dir)

    files = [p for p in variant_dir.iterdir() if p.name not in IGNORED]
    for child in files:
        if child.is_dir():
            problems.append(f"{rel}: unexpected folder {child.name}/, variants are leaves")

    svgs = sorted(p for p in files if p.suffix == ".svg")
    if not svgs:
        problems.append(f"{rel}: has no SVG, that is the source of truth")
    elif len(svgs) > 1:
        names = ", ".join(p.name for p in svgs)
        problems.append(f"{rel}: has {len(svgs)} SVGs ({names}), expected exactly one")

    for svg in svgs:
        if svg.stem != stem:
            problems.append(f"{rel}/{svg.name}: should be named {stem}.svg")

    for raster in sorted(p for p in files if p.suffix in (".png", ".jpg")):
        match = SIZED.match(raster.stem)
        if not match:
            problems.append(
                f"{rel}/{raster.name}: needs a -<width>x<height> suffix, as in {stem}-3840x2160{raster.suffix}"
            )
            continue
        if match.group("stem") != stem:
            problems.append(f"{rel}/{raster.name}: should start with {stem}-")

        claimed = (int(match.group("width")), int(match.group("height")))
        actual = image_size(raster)
        if actual is None:
            problems.append(f"{rel}/{raster.name}: could not be read as {raster.suffix[1:]}")
        elif actual != claimed:
            problems.append(
                f"{rel}/{raster.name}: is really {actual[0]}x{actual[1]}, "
                f"but the name claims {claimed[0]}x{claimed[1]}"
            )

    for stray in sorted(p for p in files if p.is_file() and p.suffix not in (".svg", ".png", ".jpg")):
        problems.append(f"{rel}/{stray.name}: unexpected file, only .svg, .png and .jpg belong here")


def check_names(platform_dir, problems):
    """Every folder between the platform and the variant has to be well named."""
    for path in sorted(platform_dir.rglob("*")):
        if not path.is_dir():
            continue
        parts = path.relative_to(platform_dir).parts
        rel = path.relative_to(REPO).as_posix()
        if len(parts) > DEPTH:
            problems.append(f"{rel}: nested too deep, expected <set>/<number>/<variant>")
            continue
        name = parts[-1]
        if len(parts) == 2:
            if not NUMBER.match(name):
                problems.append(f"{rel}: the second level should be a number, as in 1")
        elif not NAME.match(name):
            problems.append(f"{rel}: use lowercase letters, digits and hyphens")


def main():
    if not WALLPAPERS.is_dir():
        print("No wallpapers/ folder.")
        return 1

    problems = []
    variants = 0

    for child in sorted(WALLPAPERS.iterdir()):
        if child.is_file() and child.name not in IGNORED:
            problems.append(
                f"{child.relative_to(REPO).as_posix()}: loose file, wallpapers go in a platform folder"
            )
        elif child.is_dir() and child.name not in PLATFORMS:
            problems.append(
                f"{child.relative_to(REPO).as_posix()}: unknown platform, expected one of {', '.join(PLATFORMS)}"
            )

    for platform in PLATFORMS:
        platform_dir = WALLPAPERS / platform
        if not platform_dir.is_dir():
            problems.append(f"wallpapers/{platform}/ is missing")
            continue

        check_names(platform_dir, problems)

        for path in sorted(platform_dir.rglob("*")):
            if not path.is_dir():
                continue
            if len(path.relative_to(platform_dir).parts) != DEPTH:
                continue
            variants += 1
            check_variant(path, platform_dir, problems)

    if problems:
        print(f"Found {len(problems)} problem(s):\n")
        for problem in problems:
            print(f"  {problem}")
        print("\nSee the layout rules in CONTRIBUTING.md.")
        return 1

    print(f"Checked {variants} variant folder(s), layout is fine.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
