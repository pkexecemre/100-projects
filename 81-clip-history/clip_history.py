#!/usr/bin/env python3
"""Snapshot clipboard text into a deduplicated local history."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

DEFAULT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clip-history.json")
MAX_ENTRIES = 500
PREVIEW = 100


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return []
    except (OSError, ValueError) as exc:
        sys.exit(f"error: cannot read {path}: {exc}")
    if not isinstance(data, list):
        sys.exit(f"error: {path} must contain a JSON list")
    entries = []
    for item in data:
        if isinstance(item, dict) and isinstance(item.get("text"), str):
            try:
                stamp = float(item.get("ts", 0))
            except (TypeError, ValueError):
                stamp = 0.0
            entries.append({"text": item["text"], "ts": stamp})
    return entries


def save(path, entries):
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(entries[-MAX_ENTRIES:], fh, indent=1)
        fh.write("\n")
    os.replace(tmp, path)


def record(entries, text, ts=None):
    """Store text as newest, removing older copies. Returns added/duplicate."""
    if entries and entries[-1]["text"] == text:
        return "duplicate"
    entries[:] = [entry for entry in entries if entry["text"] != text]
    entries.append({"text": text, "ts": time.time() if ts is None else ts})
    return "added"


def preview(text):
    flat = " ".join(text.split())
    if len(flat) > PREVIEW:
        flat = flat[: PREVIEW - 3] + "..."
    return flat


def show(entries, limit=None, query=None, out=sys.stdout):
    items = list(reversed(entries))
    if query:
        needle = query.lower()
        items = [entry for entry in items if needle in entry["text"].lower()]
    if limit is not None:
        items = items[:limit]
    for index, entry in enumerate(items, 1):
        stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(entry["ts"]))
        out.write(f"{index:3d}  {stamp}  {preview(entry['text'])}\n")
    return len(items)


def clipboard_commands():
    commands = []
    if shutil.which("wl-paste"):
        commands.append(["wl-paste", "--no-newline"])
    if shutil.which("xclip"):
        commands.append(["xclip", "-selection", "clipboard", "-o"])
    return commands


def grab():
    commands = clipboard_commands()
    errors = []
    for command in commands:
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(f"{command[0]}: {exc}")
            continue
        if result.returncode == 0:
            return result.stdout.rstrip("\n")
        errors.append(f"{command[0]} exited with status {result.returncode}")
    if not commands:
        raise RuntimeError("no clipboard tool found; install wl-clipboard or xclip")
    raise RuntimeError("could not read clipboard: " + "; ".join(errors))


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
        path = os.path.join(tmp, "history.json")
        entries = load(path)
        assert record(entries, "alpha", ts=1) == "added"
        assert record(entries, "beta", ts=2) == "added"
        assert record(entries, "alpha", ts=3) == "added"
        assert [entry["text"] for entry in entries] == ["beta", "alpha"]
        assert record(entries, "alpha", ts=4) == "duplicate"
        save(path, entries)
        assert load(path) == entries
        assert preview("a\nb\tc") == "a b c"
        assert preview("x" * 200).endswith("...")
        commands = clipboard_commands()
        assert all(isinstance(command, list) for command in commands)
    print("self-test OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Snapshot clipboard text into a deduplicated local history.",
        epilog="Reads from wl-paste when available, otherwise xclip. Exit codes: "
        "0 success, 1 clipboard or storage error, 2 usage error.",
    )
    ap.add_argument("--file", default=DEFAULT_FILE, help="history JSON file")
    ap.add_argument("--self-test", action="store_true", help="run built-in checks")
    sub = ap.add_subparsers(dest="command", metavar="command")
    sub.add_parser("snapshot", help="read the clipboard and store it")
    list_parser = sub.add_parser("list", help="show newest entries first")
    list_parser.add_argument("-n", "--limit", type=positive, metavar="N")
    search_parser = sub.add_parser("search", help="case-insensitive text search")
    search_parser.add_argument("query", nargs="+", metavar="TEXT")
    sub.add_parser("clear", help="delete the history file")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.command:
        ap.print_help()
        return 2

    entries = load(args.file)
    if args.command == "snapshot":
        try:
            text = grab()
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if not text.strip():
            print("error: clipboard is empty", file=sys.stderr)
            return 1
        if record(entries, text) == "duplicate":
            print("already the newest entry")
            return 0
        save(args.file, entries)
        print("saved: " + preview(text))
        return 0

    if args.command == "list":
        if not show(entries, args.limit):
            print("history is empty")
        return 0

    if args.command == "search":
        query = " ".join(args.query)
        if not show(entries, query=query):
            print(f"no matches for: {query}")
            return 1
        return 0

    if os.path.exists(args.file):
        try:
            os.remove(args.file)
        except OSError as exc:
            print(f"error: cannot remove {args.file}: {exc}", file=sys.stderr)
            return 1
        print("history cleared")
    else:
        print("history is already empty")
    return 0


if __name__ == "__main__":
    sys.exit(main())
