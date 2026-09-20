#!/usr/bin/env python3
"""Check every SVG in wallpapers/ and source/ for anything but plain drawing markup.

Enforces the SVG rules from CONTRIBUTING.md: no scripting, no embedded HTML, no
network requests, no external entities, no embedded bitmaps. Prints one line per
problem and exits non-zero if there is at least one.
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SEARCH_DIRS = ("wallpapers", "source")

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

# Elements that execute, pull in remote documents, or embed non-drawing content.
FORBIDDEN_TAGS = {
    "script": "executes JavaScript",
    "foreignObject": "embeds HTML inside the drawing",
    "iframe": "embeds a remote document",
    "embed": "embeds a remote document",
    "object": "embeds a remote document",
    "audio": "embeds media",
    "video": "embeds media",
    "animation": "embeds media",
    "handler": "runs an event handler",
    "listener": "runs an event handler",
}

# Attributes that can point somewhere, checked against ALLOWED_REF.
REF_ATTRS = ("href", f"{{{XLINK_NS}}}href", "src", "xlink:href")

# A reference is fine when it points inside this same file.
ALLOWED_REF = re.compile(r"^#[^\s]*$")

URL_FUNC = re.compile(r"url\(\s*['\"]?([^)'\"]+)", re.IGNORECASE)
CSS_IMPORT = re.compile(r"@import", re.IGNORECASE)
# A plain SVG 1.1 doctype is what most editors emit and is fine. An internal
# subset is not: that is where entity attacks live.
DOCTYPE_SUBSET = re.compile(r"<!DOCTYPE[^>\[]*\[", re.IGNORECASE)
ENTITY = re.compile(r"<!ENTITY", re.IGNORECASE)


def local_name(tag):
    return tag.split("}", 1)[-1] if "}" in tag else tag


def describe_ref(value):
    """Return why a reference is not allowed, or None if it is fine."""
    value = value.strip()
    if not value or ALLOWED_REF.match(value):
        return None
    lowered = value.lower()
    if lowered.startswith("data:image/svg+xml"):
        return "embeds an SVG through a data: URI"
    if lowered.startswith("data:"):
        return "embeds a bitmap or other data through a data: URI"
    return f"points outside the file ({value[:60]})"


def check_css(text, where, problems):
    if CSS_IMPORT.search(text):
        problems.append(f"{where}: @import pulls in a remote stylesheet")
    for match in URL_FUNC.finditer(text):
        reason = describe_ref(match.group(1))
        if reason:
            problems.append(f"{where}: url() {reason}")


def check_tree(root, path, problems):
    for element in root.iter():
        tag = local_name(element.tag)
        where = f"{path}: <{tag}>"

        reason = FORBIDDEN_TAGS.get(tag)
        if reason:
            problems.append(f"{where} {reason}")
            continue

        if tag == "style" and element.text:
            check_css(element.text, where, problems)

        for name, value in element.attrib.items():
            attr = local_name(name)

            if attr.startswith("on"):
                problems.append(f"{where} has the event handler {attr}")
                continue

            if name in REF_ATTRS or attr in ("href", "src"):
                ref_reason = describe_ref(value)
                if ref_reason:
                    problems.append(f"{where} {attr} {ref_reason}")

            if attr in ("style", "filter", "fill", "stroke", "mask", "clip-path"):
                check_css(value, f"{where} {attr}", problems)


def check_svg(path):
    problems = []
    rel = path.relative_to(REPO).as_posix()
    raw = path.read_text(encoding="utf-8", errors="replace")

    for line_number, line in enumerate(raw.splitlines(), start=1):
        if ENTITY.search(line):
            problems.append(f"{rel}:{line_number}: declares an XML entity")
        elif DOCTYPE_SUBSET.search(line):
            problems.append(f"{rel}:{line_number}: DOCTYPE carries an internal subset")

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as error:
        problems.append(f"{rel}: is not well-formed XML ({error})")
        return problems

    if local_name(root.tag) != "svg":
        problems.append(f"{rel}: root element is <{local_name(root.tag)}>, not <svg>")
        return problems

    check_tree(root, rel, problems)
    return problems


def main():
    files = sorted(
        path
        for directory in SEARCH_DIRS
        for path in (REPO / directory).rglob("*.svg")
        if path.is_file()
    )

    if not files:
        print("No SVGs to check.")
        return 0

    problems = []
    for path in files:
        problems.extend(check_svg(path))

    if problems:
        print(f"Found {len(problems)} problem(s) in {len(files)} SVG(s):\n")
        for problem in problems:
            print(f"  {problem}")
        print("\nSee the SVG rules in CONTRIBUTING.md.")
        return 1

    print(f"Checked {len(files)} SVG(s), all clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
