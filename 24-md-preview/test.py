#!/usr/bin/env python3
"""Smoke test for 24-md-preview (static web app)."""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = ("index.html", "style.css", "app.js", "README.md")
MARKERS = {
    "index.html": ('id="editor"', 'id="preview"', "**bold**"),
    "app.js": ("renderMarkdown", "<strong>", "<blockquote>", "<code>"),
}
URL_RE = re.compile(r"https?://", re.IGNORECASE)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    errors = []
    texts = {}
    for name in FILES:
        path = ROOT / name
        if not path.is_file():
            errors.append(f"missing {name}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        texts[name] = text
        if not text.strip():
            errors.append(f"{name} is empty")

    readme = ROOT / "README.md"
    if readme.is_file() and readme.stat().st_size < 120:
        errors.append("README.md is shorter than 120 bytes")

    for name, markers in MARKERS.items():
        for marker in markers:
            if name in texts and marker not in texts[name]:
                errors.append(f"{name} missing marker: {marker}")

    for name in ("index.html", "style.css", "app.js"):
        if name not in texts:
            continue
        match = URL_RE.search(texts[name])
        if match:
            line = texts[name].count("\n", 0, match.start()) + 1
            errors.append(f"{name}:{line} references an external URL")
        if "fetch(" in texts[name]:
            errors.append(f"{name} uses fetch()")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: 24-md-preview (files, markers, no external URLs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
