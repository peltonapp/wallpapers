#!/usr/bin/env python3
"""Generate the gallery section of README.md from the wallpapers/ directory.

Every variant folder under wallpapers/<platform>/ becomes one gallery entry: a
JPEG is shown as the preview, and each rendered resolution is offered as a PNG
and JPEG download, plus the SVG when the master is a vector one. Authors come
from git history, co-authors first.

The same data is written to wallpapers.json for the app or a site to read.

Only the part of README.md between the START and END markers is rewritten,
so the rest of the file stays hand-editable.
"""

import html
import json
import re
import subprocess
from pathlib import Path

# Same directory, so the master naming stays in one place.
from render_exports import MASTER_SUFFIX

REPO = Path(__file__).resolve().parent.parent
WALLPAPERS = REPO / "wallpapers"
OUTPUT = REPO / "README.md"
MANIFEST = REPO / "wallpapers.json"
COLUMNS = 2
START = "<!-- gallery:start -->"
END = "<!-- gallery:end -->"


def run_git(*args):
    result = subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def authors_for(paths):
    """Return the authors of the newest commit touching any of the paths.

    Co-authors from the commit trailer come first, then the commit author.
    """
    newest_time = -1
    newest = None
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        out = run_git("log", "-1", "--format=%at%n%an%n%b", "--", rel)
        if not out:
            continue
        lines = out.split("\n")
        try:
            timestamp = int(lines[0])
        except (IndexError, ValueError):
            continue
        if timestamp > newest_time:
            newest_time = timestamp
            newest = lines
    if not newest:
        return []

    author = newest[1].strip()
    co_authors = []
    for line in newest[2:]:
        line = line.strip()
        if not line.lower().startswith("co-authored-by:"):
            continue
        value = line.split(":", 1)[1].strip()
        name = value.split("<", 1)[0].strip().rstrip(",")
        if name and name not in co_authors:
            co_authors.append(name)

    names = co_authors + ([author] if author and author not in co_authors else [])
    return names


def humanize(name):
    return " ".join(word.capitalize() for word in name.replace("_", "-").split("-"))


def collect():
    """Return {category: [entry, ...]} for every top-level folder.

    A category with no variant folders yet maps to an empty list and is still
    listed in the gallery.
    """
    categories = {}
    if not WALLPAPERS.is_dir():
        return categories

    for category_dir in sorted(p for p in WALLPAPERS.iterdir() if p.is_dir()):
        entries = []
        for variant_dir in sorted(p for p in category_dir.rglob("*") if p.is_dir()):
            sizes = sizes_in(variant_dir)
            if not sizes:
                continue
            master = master_in(variant_dir)
            parts = variant_dir.relative_to(category_dir).parts
            present = [size["jpeg"] for size in sizes] + [p for p in [master] if p]
            entries.append(
                {
                    "platform": category_dir.name,
                    "path": variant_dir.relative_to(REPO).as_posix(),
                    "parts": parts,
                    "title": " / ".join(humanize(part) for part in parts),
                    "sizes": sizes,
                    "master": master,
                    "authors": authors_for(present),
                }
            )
        categories[humanize(category_dir.name)] = entries
    return categories


def master_in(variant_dir):
    """The variant's master file: an SVG, or a -master raster for drawn art."""
    svg = next(iter(sorted(variant_dir.glob("*.svg"))), None)
    if svg is not None:
        return svg
    return next(
        (
            path
            for path in sorted(variant_dir.iterdir())
            if path.suffix in (".png", ".jpg") and path.stem.endswith(MASTER_SUFFIX)
        ),
        None,
    )


def sizes_in(variant_dir):
    """Group the exports in a folder by resolution, largest first."""
    by_resolution = {}
    for raster in sorted(variant_dir.iterdir()):
        if raster.suffix not in (".png", ".jpg"):
            continue
        match = re.search(r"-(\d{3,5})x(\d{3,5})$", raster.stem)
        if not match:
            continue
        key = (int(match.group(1)), int(match.group(2)))
        entry = by_resolution.setdefault(
            key, {"width": key[0], "height": key[1], "png": None, "jpeg": None}
        )
        entry["png" if raster.suffix == ".png" else "jpeg"] = raster

    # A resolution without a JPEG cannot be previewed or offered as one.
    return [
        by_resolution[key]
        for key in sorted(by_resolution, reverse=True)
        if by_resolution[key]["jpeg"]
    ]


def link(path):
    return path.relative_to(REPO).as_posix()


def cell(entry):
    if entry is None:
        return "<td></td>"

    sizes = entry["sizes"]
    # Preview with the smallest JPEG so the README stays light, link the largest.
    preview = link(sizes[-1]["jpeg"])
    full = link(sizes[0]["jpeg"])

    rows = []
    for size in sizes:
        formats = [
            f'<a href="{link(size[key])}?raw=1">{label}</a>'
            for label, key in (("PNG", "png"), ("JPEG", "jpeg"))
            if size[key] is not None
        ]
        rows.append(f'{size["width"]}x{size["height"]}: {" | ".join(formats)}')
    master = entry["master"]
    if master is not None and master.suffix == ".svg":
        rows.append(f'Vector: <a href="{link(master)}?raw=1">SVG</a>')

    authors = ", ".join(html.escape(name) for name in entry["authors"]) or "Unknown"

    return (
        '<td width="50%" valign="top" align="center">'
        f'<a href="{full}?raw=1"><img src="{preview}" alt="{html.escape(entry["title"])}" width="100%"></a>'
        f'<br><b>{html.escape(entry["title"])}</b>'
        f"<br><sub>Author: {authors}</sub>"
        f'<br><sub>{"<br>".join(rows)}</sub>'
        "</td>"
    )


def render(categories):
    lines = [
        "<!-- Generated by scripts/generate_gallery.py. Do not edit this section by hand. -->",
        "",
    ]

    if not categories:
        lines.append("*Nothing here yet.*")
        return "\n".join(lines)

    for category, entries in categories.items():
        lines.append(f"### {category}")
        lines.append("")
        if not entries:
            lines.append("*Nothing here yet.*")
            lines.append("")
            continue
        lines.append("<table>")
        for index in range(0, len(entries), COLUMNS):
            row = entries[index : index + COLUMNS]
            row += [None] * (COLUMNS - len(row))
            lines.append("<tr>")
            for entry in row:
                lines.append(cell(entry))
            lines.append("</tr>")
        lines.append("</table>")
        lines.append("")

    return "\n".join(lines)


def manifest(categories):
    """The same data as the gallery, for the app or a site to consume."""
    wallpapers = []
    for entries in categories.values():
        for entry in entries:
            set_name, number, variant = (list(entry["parts"]) + [None, None, None])[:3]
            wallpapers.append(
                {
                    "id": entry["path"].removeprefix("wallpapers/").replace("/", "-"),
                    "platform": entry["platform"],
                    "set": set_name,
                    "number": number,
                    "variant": variant,
                    "title": entry["title"],
                    "path": entry["path"],
                    "authors": entry["authors"],
                    "master": {
                        "kind": "vector" if entry["master"].suffix == ".svg" else "raster",
                        "path": link(entry["master"]),
                    }
                    if entry["master"]
                    else None,
                    "exports": [
                        {
                            "width": size["width"],
                            "height": size["height"],
                            "png": link(size["png"]) if size["png"] else None,
                            "jpeg": link(size["jpeg"]) if size["jpeg"] else None,
                        }
                        for size in entry["sizes"]
                    ],
                }
            )

    return {
        "note": "Generated by scripts/generate_gallery.py. Do not edit by hand.",
        "license": "CC-BY-4.0",
        "repository": "https://github.com/peltonapp/wallpapers",
        "count": len(wallpapers),
        "wallpapers": wallpapers,
    }


def main():
    readme = OUTPUT.read_text(encoding="utf-8")
    before, start, rest = readme.partition(START)
    _, end, after = rest.partition(END)
    if not start or not end:
        raise SystemExit(
            f"{OUTPUT.name} is missing the {START} / {END} markers, nothing to fill."
        )

    categories = collect()
    gallery = render(categories)
    OUTPUT.write_text(
        f"{before}{START}\n\n{gallery.rstrip()}\n\n{END}{after}", encoding="utf-8"
    )
    print(f"Wrote the gallery section of {OUTPUT.relative_to(REPO)}")

    MANIFEST.write_text(
        json.dumps(manifest(categories), indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {MANIFEST.relative_to(REPO)}")


if __name__ == "__main__":
    main()
