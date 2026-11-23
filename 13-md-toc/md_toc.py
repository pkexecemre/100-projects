#!/usr/bin/env python3
"""Build a GitHub-style Markdown table of contents from headings."""

import argparse
import re
import sys
import unicodedata

FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")


def clean_inline(text):
    """Turn inline Markdown into the plain text GitHub renders."""
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("`", "")
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"\1", text)
    text = re.sub(r"~~(.+?)~~", r"\1", text)
    text = text.replace("*", "")
    text = re.sub(r"\\([\\`*{}\[\]()#+\-.!_>])", r"\1", text)
    return text.strip()


def slugify(text):
    """Approximate github-slugger: lowercase, drop punctuation, spaces to hyphens."""
    text = clean_inline(text).lower()
    kept = []
    for char in text:
        if char.isalnum() or char in "-_":
            kept.append(char)
        elif char.isspace():
            kept.append("-")
        elif unicodedata.category(char).startswith("P"):
            continue
        # Symbols and control characters are dropped, as GitHub does.
    return "".join(kept)


def headings(text, max_depth=6):
    """Extract (level, display text, anchor) tuples, skipping fenced code."""
    found = []
    fence = None
    for line in text.splitlines():
        fence_match = FENCE_RE.match(line)
        if fence:
            if (fence_match and fence_match.group(1)[0] == fence[0]
                    and len(fence_match.group(1)) >= len(fence)):
                fence = None
            continue
        if fence_match:
            fence = fence_match.group(1)
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        level = len(match.group(1))
        if level > max_depth:
            continue
        display = clean_inline(match.group(2))
        if not display:
            continue
        found.append((level, display, slugify(display)))
    return found


def build_toc(items):
    """Render nested bullet links, numbering duplicate anchors like GitHub."""
    if not items:
        return ""
    seen = {}
    base = min(level for level, _, _ in items)
    lines = []
    for level, display, anchor in items:
        count = seen.get(anchor, 0)
        seen[anchor] = count + 1
        unique = anchor if count == 0 else "%s-%d" % (anchor, count)
        indent = "  " * (level - base)
        lines.append("%s- [%s](#%s)" % (indent, display, unique))
    return "\n".join(lines)


def self_test():
    sample = """# Project

Intro.

```sh
# not a heading
```

## Install & Run

### Use `--fast` mode

## Install & Run

#### [Link](https://example.com) heading

Setext heading
--------------
"""
    items = headings(sample)
    assert [item[0] for item in items] == [1, 2, 3, 2, 4]
    assert items[0][2] == "project"
    assert items[1][2] == "install--run"
    assert items[2][1] == "Use --fast mode"
    assert items[2][2] == "use---fast-mode"
    toc = build_toc(items)
    lines = toc.splitlines()
    assert lines[0] == "- [Project](#project)"
    assert lines[1] == "  - [Install & Run](#install--run)"
    assert lines[2] == "    - [Use --fast mode](#use---fast-mode)"
    assert lines[3] == "  - [Install & Run](#install--run-1)"
    assert lines[4] == "      - [Link heading](#link-heading)"
    assert "[Link heading]" in toc and "https://" not in toc
    assert headings(sample, max_depth=2) == items[:2] + items[3:4]
    assert build_toc([]) == ""
    assert slugify("Über café") == "über-café"
    assert headings("## C#\n")[0][1] == "C#"
    assert headings("## Done ###\n")[0][1] == "Done"
    assert headings("## foo_bar\n")[0][2] == "foo_bar"
    assert headings("## _italic_ text\n")[0][1] == "italic text"
    print("self-test: 17 checks passed")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate a Markdown table of contents with GitHub anchors.")
    parser.add_argument("file", nargs="?", default="-",
                        help="Markdown file, or - for stdin (default)")
    parser.add_argument("--max-depth", type=int, default=6, metavar="N",
                        help="deepest heading level to include (default 6)")
    parser.add_argument("--self-test", action="store_true",
                        help="run offline checks and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        self_test()
        return 0
    if not 1 <= args.max_depth <= 6:
        parser.error("--max-depth must be between 1 and 6")

    try:
        if args.file == "-":
            text = sys.stdin.read()
        else:
            with open(args.file, encoding="utf-8") as handle:
                text = handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        print("md-toc: error: %s" % exc, file=sys.stderr)
        return 2

    toc = build_toc(headings(text, args.max_depth))
    if toc:
        print(toc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
