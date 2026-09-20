#!/usr/bin/env python3
"""Generate the gallery section of README.md from the wallpapers/ directory.

Layout expected:

    wallpapers/<category>/<set>/<variant>/<name>-<size>.jpg
                                          <name>-<size>.png
                                          <name>.svg

Every variant folder becomes one gallery entry: the JPEG is shown as the
preview, and PNG / JPEG / SVG are offered as downloads. Authors come from
git history, co-authors first.

Only the part of README.md between the START and END markers is rewritten,
so the rest of the file stays hand-editable.
"""

import html
import re
import struct
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WALLPAPERS = REPO / "wallpapers"
OUTPUT = REPO / "README.md"
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


def png_size(path):
    """Read width and height out of a PNG header, or None if it is not a PNG."""
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
    except OSError:
        return None
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    width, height = struct.unpack(">II", header[16:24])
    return f"{width}x{height}"


def resolution_for(entry_paths):
    """Resolution of a variant, from the filename if present, else the PNG header."""
    for path in entry_paths:
        match = re.search(r"(\d{3,5}x\d{3,5})", path.stem)
        if match:
            return match.group(1)
    for path in entry_paths:
        size = png_size(path)
        if size:
            return size
    return None


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
            jpeg = next(iter(sorted(variant_dir.glob("*.jpg"))), None)
            if jpeg is None:
                continue
            png = next(iter(sorted(variant_dir.glob("*.png"))), None)
            svg = next(iter(sorted(variant_dir.glob("*.svg"))), None)
            parts = variant_dir.relative_to(category_dir).parts
            present = [p for p in (jpeg, png, svg) if p]
            entries.append(
                {
                    "title": " / ".join(humanize(part) for part in parts),
                    "jpeg": jpeg,
                    "png": png,
                    "svg": svg,
                    "resolution": resolution_for(present),
                    "authors": authors_for(present),
                }
            )
        categories[humanize(category_dir.name)] = entries
    return categories


def link(path):
    return path.relative_to(REPO).as_posix()


def cell(entry):
    if entry is None:
        return "<td></td>"

    preview = link(entry["jpeg"])
    downloads = []
    for label, key in (("PNG", "png"), ("JPEG", "jpeg"), ("SVG", "svg")):
        path = entry[key]
        if path is not None:
            downloads.append(f'<a href="{link(path)}?raw=1">{label}</a>')

    authors = ", ".join(html.escape(name) for name in entry["authors"]) or "Unknown"
    meta = [f"Author: {authors}"]
    if entry["resolution"]:
        meta.insert(0, entry["resolution"])

    return (
        '<td width="50%" valign="top" align="center">'
        f'<a href="{preview}?raw=1"><img src="{preview}" alt="{html.escape(entry["title"])}" width="100%"></a>'
        f'<br><b>{html.escape(entry["title"])}</b>'
        f'<br><sub>{" &middot; ".join(meta)}</sub>'
        f'<br>{" | ".join(downloads)}'
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


def main():
    readme = OUTPUT.read_text(encoding="utf-8")
    before, start, rest = readme.partition(START)
    _, end, after = rest.partition(END)
    if not start or not end:
        raise SystemExit(
            f"{OUTPUT.name} is missing the {START} / {END} markers, nothing to fill."
        )

    gallery = render(collect())
    OUTPUT.write_text(
        f"{before}{START}\n\n{gallery.rstrip()}\n\n{END}{after}", encoding="utf-8"
    )
    print(f"Wrote the gallery section of {OUTPUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
