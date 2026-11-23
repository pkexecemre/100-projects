#!/usr/bin/env python3
"""Hash a directory tree into a JSON baseline and later report drift."""

import argparse
import datetime
import hashlib
import json
import os
import stat
import sys

SKIP_DIRS = {".git", "__pycache__", "node_modules"}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def collect(root, baseline_path):
    root_abs = os.path.abspath(root)
    baseline_abs = os.path.abspath(baseline_path) if baseline_path else None
    entries = {}
    errors = []
    for dirpath, dirnames, filenames in os.walk(root_abs):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            full_abs = os.path.abspath(full)
            if baseline_abs and full_abs == baseline_abs:
                continue
            try:
                st = os.lstat(full)
                if not stat.S_ISREG(st.st_mode) or stat.S_ISLNK(st.st_mode):
                    continue
                rel = os.path.relpath(full_abs, root_abs)
                entries[rel] = {
                    "sha256": sha256_file(full_abs),
                    "size": st.st_size,
                    "mode": oct(stat.S_IMODE(st.st_mode)),
                    "mtime": int(st.st_mtime),
                }
            except OSError as exc:
                errors.append(str(exc))
    return root_abs, entries, errors


def cmd_create(root, baseline):
    if not os.path.isdir(root):
        raise ValueError("not a directory: %s" % root)
    root_abs, entries, errors = collect(root, baseline)
    doc = {
        "version": 1,
        "root": root_abs,
        "created": datetime.datetime.now(datetime.timezone.utc)
                   .isoformat(timespec="seconds"),
        "count": len(entries),
        "entries": entries,
    }
    tmp = baseline + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, baseline)
    for err in errors:
        print("warning: %s" % err, file=sys.stderr)
    print("baseline %s: %d file(s) from %s" % (baseline, len(entries), root_abs))
    return 0


def cmd_compare(baseline, root_override):
    try:
        with open(baseline, encoding="utf-8") as fh:
            doc = json.load(fh)
        old = doc["entries"]
        root = root_override or doc["root"]
    except (OSError, ValueError, KeyError) as exc:
        raise ValueError("cannot load baseline %s: %s" % (baseline, exc))
    if not os.path.isdir(root):
        raise ValueError("baseline root is not a directory: %s" % root)
    root_abs, current, errors = collect(root, baseline)
    added = sorted(set(current) - set(old))
    removed = sorted(set(old) - set(current))
    changed = []
    for rel in sorted(set(old) & set(current)):
        before, after = old[rel], current[rel]
        fields = [key for key in ("sha256", "size", "mode")
                  if before.get(key) != after.get(key)]
        if fields:
            changed.append({"path": rel, "fields": fields,
                            "before": {k: before.get(k) for k in fields},
                            "after": {k: after.get(k) for k in fields}})
    return {
        "baseline": os.path.abspath(baseline),
        "root": root_abs,
        "added": added,
        "removed": removed,
        "changed": changed,
        "clean": not (added or removed or changed),
        "errors": errors,
    }


def self_test():
    import subprocess
    import tempfile

    script = os.path.abspath(__file__)
    with tempfile.TemporaryDirectory() as tmp:
        tree = os.path.join(tmp, "tree")
        os.makedirs(os.path.join(tree, "sub"))
        for rel, body in (("one.txt", "one\n"), ("sub/two.txt", "two\n"),
                          ("sub/three.txt", "three\n")):
            with open(os.path.join(tree, rel), "w", encoding="utf-8") as fh:
                fh.write(body)
        baseline = os.path.join(tmp, "baseline.json")

        def run(*args):
            return subprocess.run([sys.executable, script] + list(args),
                                  capture_output=True, text=True)

        result = run("--create", baseline, tree)
        assert result.returncode == 0, result.stderr
        result = run("--compare", baseline, "--json")
        assert result.returncode == 0, result.stdout + result.stderr
        report = json.loads(result.stdout)
        assert report["clean"] is True and not report["added"], report

        with open(os.path.join(tree, "one.txt"), "a", encoding="utf-8") as fh:
            fh.write("changed\n")
        with open(os.path.join(tree, "new.txt"), "w", encoding="utf-8") as fh:
            fh.write("new\n")
        os.remove(os.path.join(tree, "sub", "three.txt"))
        result = run("--compare", baseline, "--json")
        assert result.returncode == 1, result.stdout
        report = json.loads(result.stdout)
        assert report["added"] == ["new.txt"], report["added"]
        assert report["removed"] == [os.path.join("sub", "three.txt")], report["removed"]
        assert [row["path"] for row in report["changed"]] == ["one.txt"], report["changed"]
        assert report["changed"][0]["fields"] == ["sha256", "size"], report["changed"]
        result = run("--compare", os.path.join(tmp, "nope.json"))
        assert result.returncode == 2
    print("self-test: PASS")


def main():
    ap = argparse.ArgumentParser(
        description="Create a JSON integrity baseline or compare a tree to one.")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--create", metavar="BASELINE", help="write baseline JSON")
    mode.add_argument("--compare", metavar="BASELINE", help="compare to baseline JSON")
    ap.add_argument("--root", help="override baseline root during --compare")
    ap.add_argument("--json", action="store_true", help="JSON output for --compare")
    ap.add_argument("--self-test", action="store_true", help="run built-in smoke test")
    ap.add_argument("tree", nargs="?", help="directory to hash (with --create)")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.create and not args.compare:
        ap.error("one of --create or --compare is required")
    try:
        if args.create:
            if not args.tree:
                ap.error("--create requires a directory argument")
            return cmd_create(args.tree, args.create)
        report = cmd_compare(args.compare, args.root)
    except (OSError, ValueError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("baseline: %s" % report["baseline"])
        print("root:     %s" % report["root"])
        for rel in report["added"]:
            print("ADDED    %s" % rel)
        for rel in report["removed"]:
            print("REMOVED  %s" % rel)
        for row in report["changed"]:
            print("CHANGED  %s (%s)" % (row["path"], ", ".join(row["fields"])))
        for err in report["errors"]:
            print("warning: %s" % err, file=sys.stderr)
        print("\n%s: %d added, %d removed, %d changed" %
              ("clean" if report["clean"] else "DRIFT", len(report["added"]),
               len(report["removed"]), len(report["changed"])))
    return 0 if report["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
