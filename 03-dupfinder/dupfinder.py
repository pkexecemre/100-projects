#!/usr/bin/env python3
"""Find duplicate files by size and SHA-256. Report only; deletes nothing."""

import argparse
import hashlib
import json
import os
import sys


def parse_size(text):
    """Accept bytes or a K/M/G suffix."""
    t = text.strip().upper()
    mult = 1
    if t and t[-1] in "KMG":
        mult = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3}[t[-1]]
        t = t[:-1]
    try:
        value = int(t)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid size: {text!r}")
    if value < 0:
        raise argparse.ArgumentTypeError("size must be non-negative")
    return value * mult


def iter_files(paths):
    for root in paths:
        if os.path.isfile(root) and not os.path.islink(root):
            yield root
            continue
        for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):
            dirnames.sort()
            for name in sorted(filenames):
                path = os.path.join(dirpath, name)
                if os.path.isfile(path) and not os.path.islink(path):
                    yield path


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def find_duplicates(paths, min_size):
    by_size = {}
    seen = set()
    for path in iter_files(paths):
        key = os.path.abspath(path)
        if key in seen:
            continue
        seen.add(key)
        try:
            size = os.path.getsize(path)
        except OSError:
            continue
        if size < min_size:
            continue
        by_size.setdefault(size, []).append(path)
    groups = []
    for size in sorted(by_size, reverse=True):
        candidates = by_size[size]
        if len(candidates) < 2:
            continue
        by_hash = {}
        for path in candidates:
            try:
                by_hash.setdefault(sha256(path), []).append(path)
            except OSError as exc:
                print(f"warning: cannot read {path}: {exc}", file=sys.stderr)
        for digest, files in by_hash.items():
            if len(files) > 1:
                groups.append({"size": size, "sha256": digest, "files": files})
    groups.sort(key=lambda g: (g["size"] * (len(g["files"]) - 1), g["size"]), reverse=True)
    return groups


def render(groups):
    total_wasted = sum(g["size"] * (len(g["files"]) - 1) for g in groups)
    dup_files = sum(len(g["files"]) - 1 for g in groups)
    lines = [f"{len(groups)} duplicate group(s), {dup_files} redundant file(s), "
             f"{total_wasted} bytes reclaimable"]
    for g in groups:
        lines.append(f"\n[{g['size']} bytes] {len(g['files'])} copies  {g['sha256'][:16]}")
        for path in g["files"]:
            lines.append(f"  {path}")
    return "\n".join(lines)


def self_test():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        def put(name, data):
            path = os.path.join(tmp, name)
            with open(path, "wb") as fh:
                fh.write(data)
            return path

        a = put("a.txt", b"same content")
        put("sub_b.txt", b"same content")
        put("unique.txt", b"different")
        put("empty1", b"")
        put("empty2", b"")
        groups = find_duplicates([tmp], 1)
        assert len(groups) == 1, groups
        assert sorted(groups[0]["files"]) == sorted([a, os.path.join(tmp, "sub_b.txt")])
        assert len(find_duplicates([tmp], 0)) == 2
        assert find_duplicates([a], 0) == []
        assert "reclaimable" in render(groups)
    print("self-test OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", default=["."], help="files or directories (default .)")
    ap.add_argument("--min-size", type=parse_size, default=1,
                    help="ignore files smaller than this; accepts K/M/G (default 1 byte)")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--self-test", action="store_true", help="run offline self tests")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    missing = [p for p in args.paths if not os.path.exists(p)]
    if missing:
        print(f"dupfinder: no such path: {missing[0]}", file=sys.stderr)
        return 1

    groups = find_duplicates(args.paths, args.min_size)
    wasted = sum(g["size"] * (len(g["files"]) - 1) for g in groups)
    if args.json:
        print(json.dumps({
            "groups": groups,
            "summary": {
                "groups": len(groups),
                "duplicate_files": sum(len(g["files"]) - 1 for g in groups),
                "wasted_bytes": wasted,
            },
        }, indent=2, sort_keys=True))
    else:
        print(render(groups))
    return 0


if __name__ == "__main__":
    sys.exit(main())
