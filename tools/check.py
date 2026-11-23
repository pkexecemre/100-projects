#!/usr/bin/env python3
"""Structural check for the 100-projects monorepo.

Each NN-slug/ folder needs a README.md and at least one source file.
Reports TODO/FIXME markers and empty folders.  Exits 1 on problems.
"""
import argparse
import os
import re
import sys

SRC_EXT = {".py", ".sh", ".html", ".js", ".css", ".go", ".rs", ".c", ".cpp", ".sql"}


def check(root: str, lo: int = 1, hi: int = 100) -> list[str]:
    problems: list[str] = []
    found = 0
    for name in sorted(os.listdir(root)):
        m = re.match(r"^(\d{2,3})-[a-z0-9-]+$", name)
        if not m:
            continue
        num = int(m.group(1))
        if not (lo <= num <= hi):
            continue
        found += 1
        path = os.path.join(root, name)
        if not os.path.isdir(path):
            problems.append(f"{name}: not a directory")
            continue
        readme = os.path.join(path, "README.md")
        if not os.path.isfile(readme) or os.path.getsize(readme) < 120:
            problems.append(f"{name}: missing or tiny README.md")
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        if not any(os.path.splitext(f)[1].lower() in SRC_EXT for f in files):
            problems.append(f"{name}: no source file")
        for f in files:
            if os.path.splitext(f)[1].lower() in SRC_EXT:
                try:
                    text = open(os.path.join(path, f), encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                if re.search(r"\b(TODO|FIXME)\b", text):
                    problems.append(f"{name}/{f}: contains TODO/FIXME")
    print(f"checked {found} projects")
    for p in problems:
        print("  !", p)
    return problems


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--range", default="1-100")
    ap.add_argument("root", nargs="?", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    a = ap.parse_args()
    lo, hi = map(int, a.range.split("-"))
    sys.exit(1 if check(a.root, lo, hi) else 0)
