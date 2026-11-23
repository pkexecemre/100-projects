#!/usr/bin/env python3
"""Generate the root README index from the project folders."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def summarize(path: str) -> tuple[str, str]:
    title, blurb = os.path.basename(path), ""
    try:
        text = open(os.path.join(path, "README.md"), encoding="utf-8", errors="replace").read()
    except OSError:
        return title, blurb
    lines = [line.strip() for line in text.splitlines()]
    title_at = -1
    for index, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
            title_at = index
            break
    paragraph: list[str] = []
    for line in lines[title_at + 1:]:
        if not line:
            if paragraph:
                break
            continue
        if line.startswith(("#", "```", "!", "[", ">", "|")):
            if paragraph:
                break
            continue
        paragraph.append(line)
    blurb = re.sub(r"\s+", " ", " ".join(paragraph)).strip()
    first = re.split(r"(?<=[.!?])\s+", blurb, maxsplit=1)[0]
    if len(first) >= 12:
        blurb = first
    if len(blurb) > 140:
        blurb = blurb[:137].rsplit(" ", 1)[0] + "…"
    return title, blurb


def main() -> None:
    rows = []
    for name in os.listdir(ROOT):
        if not re.match(r"^\d{2,3}-[a-z0-9-]+$", name):
            continue
        path = os.path.join(ROOT, name)
        if not os.path.isdir(path):
            continue
        title, blurb = summarize(path)
        rows.append((int(name.split("-", 1)[0]), name, title, blurb))
    rows.sort(key=lambda row: row[0])
    out = [
        "# 100 Projects",
        "",
        "A collection of 100 small, self-contained projects: CLI tools, web toys,",
        "terminal games, converters and utilities. Every folder has its own README,",
        "runnable code and a smoke test. Python 3 standard library only; web projects",
        "are plain HTML/CSS/JS with no build step.",
        "",
        f"**{len(rows)} projects** · built with parallel agents · no third-party dependencies.",
        "",
        "## Index",
        "",
        "| # | Folder | What it does |",
        "|---|--------|--------------|",
    ]
    for num, name, title, blurb in rows:
        out.append(f"| {num:02d} | [`{name}`]({name}/) | {blurb or title} |")
    out += [
        "",
        "## Running",
        "",
        "```sh",
        "cd 01-disk-alert && python3 disk_alert.py --help",
        "cd 21-palette && python3 -m http.server 8000   # open http://localhost:8000",
        "```",
        "",
        "Each project's README shows its exact command. Structural check:",
        "",
        "```sh",
        "python3 tools/check.py",
        "```",
        "",
        "## License",
        "",
        "MIT — see [LICENSE](LICENSE).",
        "",
    ]
    with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    print(f"wrote README.md with {len(rows)} projects")


if __name__ == "__main__":
    main()
