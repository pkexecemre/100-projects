#!/usr/bin/env python3
"""Recursive, context-aware search over a directory of notes."""

import argparse
import io
import os
import re
import sys
import tempfile

SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv"}
MAX_FILE_BYTES = 2 * 1024 * 1024


def is_binary(path):
    try:
        with open(path, "rb") as fh:
            return b"\0" in fh.read(4096)
    except OSError:
        return True


def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            name for name in dirnames
            if name not in SKIP_DIRS and not name.startswith(".")
        )
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            try:
                if os.path.getsize(path) > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            if is_binary(path):
                continue
            yield path


def highlight(line, spans, use_color):
    if not use_color or not spans:
        return line
    pieces = []
    last = 0
    for start, end in spans:
        pieces.append(line[last:start])
        pieces.append("\x1b[1;31m" + line[start:end] + "\x1b[0m")
        last = end
    pieces.append(line[last:])
    return "".join(pieces)


def search(root, pattern, context=2, ignore_case=True, color=False,
           limit=200, out=sys.stdout, err=None):
    err = sys.stderr if err is None else err
    if not os.path.isdir(root):
        raise ValueError(f"not a directory: {root}")
    flags = re.IGNORECASE if ignore_case else 0
    try:
        regex = re.compile(pattern, flags)
    except re.error as exc:
        raise ValueError(f"invalid pattern: {exc}")

    total = 0
    truncated = False
    for path in iter_files(root):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()
        except OSError:
            continue
        hits = {}
        for index, line in enumerate(lines):
            spans = [(match.start(), match.end()) for match in regex.finditer(line)]
            if spans:
                hits[index] = spans
        if not hits:
            continue

        groups = []
        for index in sorted(hits):
            low = max(0, index - context)
            high = min(len(lines) - 1, index + context)
            if groups and low <= groups[-1][1] + 1:
                groups[-1] = (groups[-1][0], max(groups[-1][1], high))
            else:
                groups.append((low, high))

        rel = os.path.relpath(path, root)
        for group_index, (low, high) in enumerate(groups):
            if group_index:
                out.write("--\n")
            for index in range(low, high + 1):
                if index in hits:
                    total += 1
                    if total > limit:
                        truncated = True
                        break
                    out.write(f"{rel}:{index + 1}:{highlight(lines[index], hits[index], color)}\n")
                else:
                    out.write(f"{rel}-{index + 1}-{lines[index]}\n")
            if truncated:
                break
        if truncated:
            break

    if truncated:
        err.write(f"... stopped after {limit} matches\n")
    return total


def non_negative(value):
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer")
    if number < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return number


def positive(value):
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer")
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def self_test():
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "sub"))
        with open(os.path.join(tmp, "a.txt"), "w", encoding="utf-8") as fh:
            fh.write("one\ntwo\nneedle here\nfour\nfive\n")
        with open(os.path.join(tmp, "sub", "b.md"), "w", encoding="utf-8") as fh:
            fh.write("nothing\nNEEDLE upper\n")

        buffer = io.StringIO()
        found = search(tmp, "needle", context=1, color=False, out=buffer)
        text = buffer.getvalue()
        assert found == 2
        assert "a.txt:3:needle here" in text
        assert "a.txt-2-two" in text
        assert "sub/b.md:2:NEEDLE upper" in text

        buffer = io.StringIO()
        assert search(tmp, "needle", ignore_case=False, out=buffer) == 1
        assert "a.txt:3:needle here" in buffer.getvalue()

        buffer = io.StringIO()
        assert search(tmp, "two", context=0, out=buffer) == 1
        assert buffer.getvalue() == "a.txt:2:two\n"

        buffer = io.StringIO()
        assert search(tmp, "NEEDLE", color=True, out=buffer) == 2
        assert "\x1b[1;31m" in buffer.getvalue()

        buffer = io.StringIO()
        notice = io.StringIO()
        assert search(tmp, "e", limit=2, context=0, out=buffer, err=notice) == 3
        lines = [line for line in buffer.getvalue().splitlines() if line and line != "--"]
        assert len(lines) == 2
        assert "stopped after 2 matches" in notice.getvalue()

        buffer = io.StringIO()
        assert search(tmp, "absent", out=buffer) == 0
        assert buffer.getvalue() == ""

        for bad in ("(", "missing-dir"):
            try:
                if bad == "(":
                    search(tmp, bad, out=io.StringIO())
                else:
                    search(os.path.join(tmp, bad), "x", out=io.StringIO())
            except ValueError:
                pass
            else:
                raise AssertionError(f"invalid search accepted: {bad}")
    print("self-test OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Search notes recursively with context and match highlighting.",
        epilog="Output follows grep's file:line: match and file-line- context "
        "format. Exit codes: 0 matches, 1 no matches, 2 error.",
    )
    ap.add_argument("pattern", nargs="?", help="regular expression to search for")
    ap.add_argument("directory", nargs="?", default=".", help="notes directory")
    ap.add_argument("-C", "--context", type=non_negative, default=2, metavar="N",
                    help="context lines around each match (default 2)")
    ap.add_argument("-m", "--max", type=positive, default=200, metavar="N",
                    help="stop after N matching lines (default 200)")
    ap.add_argument("-s", "--case-sensitive", action="store_true",
                    help="match case exactly")
    ap.add_argument("--color", choices=("auto", "always", "never"), default="auto",
                    help="highlight matches (default auto)")
    ap.add_argument("--self-test", action="store_true", help="run built-in checks")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.pattern:
        ap.error("a search pattern is required")

    color = args.color == "always" or (
        args.color == "auto" and sys.stdout.isatty()
    )
    try:
        found = search(
            args.directory,
            args.pattern,
            context=args.context,
            ignore_case=not args.case_sensitive,
            color=color,
            limit=args.max,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0 if found else 1


if __name__ == "__main__":
    sys.exit(main())
