#!/usr/bin/env python3
"""Create and verify sha256 manifests for files and directory trees."""

import argparse
import hashlib
import os
import sys

CHUNK = 1 << 20


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def iter_files(inputs, exclude):
    for item in inputs:
        if os.path.isdir(item) and not os.path.islink(item):
            for dirpath, dirnames, filenames in os.walk(item):
                dirnames[:] = sorted(d for d in dirnames if d not in exclude)
                for name in sorted(filenames):
                    full = os.path.join(dirpath, name)
                    if os.path.isfile(full) and not os.path.islink(full):
                        yield full
        elif os.path.isfile(item):
            yield item
        else:
            raise FileNotFoundError(item)


def cmd_create(manifest, inputs, root, exclude):
    if not inputs:
        raise ValueError("--create needs at least one file or directory")
    root_abs = os.path.abspath(root)
    manifest_abs = os.path.abspath(manifest)
    rows = []
    for full in iter_files(inputs, exclude):
        full_abs = os.path.abspath(full)
        if full_abs == manifest_abs:
            continue
        rel = os.path.relpath(full_abs, root_abs)
        rows.append((sha256_file(full_abs), rel))
    tmp = manifest + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# sha256 manifest: <digest>  <path>\n")
        for digest, rel in sorted(rows, key=lambda row: row[1]):
            fh.write("%s  %s\n" % (digest, rel))
    os.replace(tmp, manifest)
    print("created %s with %d entries" % (manifest, len(rows)))
    return 0


def read_manifest(path):
    entries = []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.rstrip("\r\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split(None, 1)
            if len(parts) != 2 or len(parts[0]) != 64:
                raise ValueError("malformed manifest line %d" % lineno)
            rel = parts[1].strip()
            if rel.startswith("*"):
                rel = rel[1:]
            entries.append((parts[0].lower(), rel))
    return entries


def cmd_check(manifest, root, verbose):
    entries = read_manifest(manifest)
    ok = missing = bad = 0
    for digest, rel in entries:
        full = rel if os.path.isabs(rel) else os.path.join(root, rel)
        if not os.path.isfile(full):
            print("MISSING  %s" % rel)
            missing += 1
            continue
        if sha256_file(full) == digest:
            ok += 1
            if verbose:
                print("OK       %s" % rel)
        else:
            print("FAILED   %s" % rel)
            bad += 1
    print("checked %d: %d ok, %d changed, %d missing" % (len(entries), ok, bad, missing))
    return 0 if bad == 0 and missing == 0 else 1


def self_test():
    import subprocess
    import tempfile

    script = os.path.abspath(__file__)
    with tempfile.TemporaryDirectory() as tmp:
        tree = os.path.join(tmp, "tree")
        os.makedirs(os.path.join(tree, "sub"))
        with open(os.path.join(tree, "a.txt"), "w", encoding="utf-8") as fh:
            fh.write("alpha\n")
        with open(os.path.join(tree, "sub", "b.txt"), "w", encoding="utf-8") as fh:
            fh.write("bravo\n")
        manifest = os.path.join(tmp, "manifest.sha256")

        def run(*args):
            return subprocess.run([sys.executable, script] + list(args),
                                  capture_output=True, text=True)

        result = run("--create", manifest, "--root", tmp, tree)
        assert result.returncode == 0, result.stderr
        result = run("--check", manifest, "--root", tmp, "--verbose")
        assert result.returncode == 0, result.stdout + result.stderr
        assert "OK" in result.stdout
        with open(os.path.join(tree, "a.txt"), "a", encoding="utf-8") as fh:
            fh.write("tampered\n")
        result = run("--check", manifest, "--root", tmp)
        assert result.returncode == 1 and "FAILED" in result.stdout, result.stdout
        os.remove(os.path.join(tree, "sub", "b.txt"))
        result = run("--check", manifest, "--root", tmp)
        assert result.returncode == 1 and "MISSING" in result.stdout, result.stdout
        result = run("--check", os.path.join(tmp, "nope.sha256"))
        assert result.returncode == 2
    print("self-test: PASS")


def main():
    ap = argparse.ArgumentParser(
        description="Create or verify a sha256 manifest of a directory tree.",
        epilog="Exit codes: 0 verified, 1 mismatch/missing, 2 usage or IO error.")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--create", metavar="MANIFEST", help="write manifest for paths")
    mode.add_argument("--check", metavar="MANIFEST", help="verify paths against manifest")
    ap.add_argument("--root", default=".", help="base for relative paths (default: .)")
    ap.add_argument("--exclude", action="append", default=[".git"],
                    help="directory name to skip (repeatable, default: .git)")
    ap.add_argument("--verbose", action="store_true", help="print OK lines too")
    ap.add_argument("--self-test", action="store_true", help="run built-in smoke test")
    ap.add_argument("paths", nargs="*", help="files/directories for --create")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.create and not args.check:
        ap.error("one of --create or --check is required")
    try:
        if args.create:
            return cmd_create(args.create, args.paths, args.root, set(args.exclude))
        if args.paths:
            ap.error("--check takes no path arguments; use --root")
        return cmd_check(args.check, args.root, args.verbose)
    except (OSError, ValueError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
