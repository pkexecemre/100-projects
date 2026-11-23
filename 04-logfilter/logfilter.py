#!/usr/bin/env python3
"""Filter log lines from stdin or a file by regex, level token and tail count."""

import argparse
import re
import sys

LEVELS = {
    "trace": r"TRACE",
    "debug": r"DEBUG",
    "info": r"INFO",
    "warn": r"WARN(?:ING)?",
    "warning": r"WARN(?:ING)?",
    "error": r"(?:ERROR|ERR)",
    "err": r"(?:ERROR|ERR)",
    "crit": r"(?:CRIT(?:ICAL)?|FATAL)",
    "critical": r"(?:CRIT(?:ICAL)?|FATAL)",
    "fatal": r"(?:CRIT(?:ICAL)?|FATAL)",
}

LEVEL_TOKEN = re.compile(r"\b(TRACE|DEBUG|INFO|WARN(?:ING)?|ERR(?:OR)?|CRIT(?:ICAL)?|FATAL)\b",
                         re.IGNORECASE)
COLORS = {"TRACE": "90", "DEBUG": "36", "INFO": "32", "WARN": "33",
          "WARNING": "33", "ERROR": "31", "ERR": "31", "CRIT": "35",
          "CRITICAL": "35", "FATAL": "1;31"}


def level_pattern(names):
    if not names:
        return None
    parts = []
    for name in names:
        key = name.strip().lower()
        if not key:
            raise ValueError("empty level name")
        if key not in LEVELS:
            raise ValueError(f"unknown level {name!r}; choose from {', '.join(sorted(LEVELS))}")
        parts.append(LEVELS[key])
    return re.compile(r"\b(?:" + "|".join(parts) + r")\b", re.IGNORECASE)


def select(lines, pattern, level_re, tail):
    """Yield matching lines, honouring the last-N window."""
    if tail is None:
        for line in lines:
            if pattern.search(line) and (level_re is None or level_re.search(line)):
                yield line
        return
    from collections import deque
    keep = deque(maxlen=tail)
    for line in lines:
        if pattern.search(line) and (level_re is None or level_re.search(line)):
            keep.append(line)
    yield from keep


def colorize(line):
    def paint(match):
        token = match.group(0)
        return f"\033[{COLORS.get(token.upper(), '0')}m{token}\033[0m"
    return LEVEL_TOKEN.sub(paint, line)


def use_color(mode):
    if mode == "always":
        return True
    if mode == "never":
        return False
    import os
    return sys.stdout.isatty() and "NO_COLOR" not in os.environ


def self_test():
    lines = [
        "2024-01-01 INFO started\n",
        "2024-01-01 WARNING disk low\n",
        "2024-01-01 ERROR failed thing\n",
        "2024-01-01 debug noise\n",
        "2024-01-01 FATAL bye\n",
    ]
    pat = re.compile("2024")
    warn = level_pattern(["warn"])
    err = level_pattern(["error"])
    assert [l for l in select(lines, pat, warn, None)] == [lines[1]]
    assert [l for l in select(lines, pat, err, None)] == [lines[2]]
    assert list(select(lines, pat, None, 2)) == lines[3:]
    assert list(select(lines, re.compile("nomatch"), None, None)) == []
    assert "\033[" in colorize(lines[2]) and colorize("plain") == "plain"
    try:
        level_pattern(["nope"])
    except ValueError:
        pass
    else:
        raise AssertionError("accepted invalid level")
    print("self-test OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pattern", nargs="?", help="regular expression to search for")
    ap.add_argument("file", nargs="?", help="input file (default stdin)")
    ap.add_argument("--level", action="append", metavar="NAME",
                    help="only lines with this level token; repeatable")
    ap.add_argument("--tail", type=int, metavar="N", help="print only the last N matches")
    ap.add_argument("--ignore-case", action="store_true", help="case-insensitive pattern")
    ap.add_argument("--color", choices=["auto", "always", "never"], default="auto",
                    help="colour level tokens (default auto: tty only)")
    ap.add_argument("--self-test", action="store_true", help="run offline self tests")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.pattern:
        ap.error("a pattern is required")
    if args.tail is not None and args.tail < 0:
        ap.error("--tail must be >= 0")
    try:
        pattern = re.compile(args.pattern, re.IGNORECASE if args.ignore_case else 0)
        level_re = level_pattern(args.level)
    except re.error as exc:
        ap.error(f"bad regex: {exc}")
    except ValueError as exc:
        ap.error(str(exc))

    if args.file:
        try:
            fh = open(args.file, encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"logfilter: {exc}", file=sys.stderr)
            return 1
    else:
        fh = sys.stdin

    paint = use_color(args.color)
    try:
        for line in select(fh, pattern, level_re, args.tail):
            sys.stdout.write(colorize(line) if paint else line)
            if not line.endswith("\n"):
                sys.stdout.write("\n")
    except BrokenPipeError:
        return 0
    except OSError as exc:
        print(f"logfilter: read error: {exc}", file=sys.stderr)
        return 1
    finally:
        if args.file:
            fh.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
