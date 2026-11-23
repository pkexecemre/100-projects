#!/usr/bin/env python3
"""Regex-rename files in a directory. Dry-run unless --apply is given."""

import argparse
import os
import re
import sys


class RenameError(Exception):
    pass


def plan_renames(directory, pattern, replacement):
    """Return [(old_name, new_name)] after validating every target."""
    plans = []
    problems = []
    for name in sorted(os.listdir(directory)):
        source = os.path.join(directory, name)
        if not os.path.isfile(source):
            continue
        try:
            new_name = pattern.sub(replacement, name)
        except re.error as exc:
            raise RenameError(f"replacement failed for {name!r}: {exc}") from exc
        if new_name == name:
            continue
        if new_name in ("", ".", ".."):
            problems.append(f"refusing empty or dot target for {name!r}")
            continue
        if "/" in new_name or os.sep in new_name:
            problems.append(f"refusing target with a path separator: {new_name!r}")
            continue
        plans.append((name, new_name))

    targets = {}
    for old_name, new_name in plans:
        target = os.path.join(directory, new_name)
        if new_name in targets:
            problems.append(f"two files would become {new_name!r}: "
                            f"{targets[new_name]!r} and {old_name!r}")
        else:
            targets[new_name] = old_name
        if os.path.lexists(target) and new_name != old_name:
            problems.append(f"target already exists: {new_name!r}")
    if problems:
        raise RenameError("\n".join(problems))
    return plans


def apply_renames(directory, plans):
    done, failed = [], []
    for old_name, new_name in plans:
        try:
            os.rename(os.path.join(directory, old_name),
                      os.path.join(directory, new_name))
            done.append((old_name, new_name))
        except OSError as exc:
            failed.append((old_name, new_name, str(exc)))
    return done, failed


def self_test():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        for name in ("report 1.txt", "report 2.txt", "keep.md"):
            open(os.path.join(tmp, name), "w").close()
        pattern = re.compile(r"^report (\d+)\.txt$")
        plans = plan_renames(tmp, pattern, r"doc-\1.txt")
        assert plans == [("report 1.txt", "doc-1.txt"), ("report 2.txt", "doc-2.txt")], plans
        assert "doc-1.txt" not in os.listdir(tmp)
        done, failed = apply_renames(tmp, plans)
        assert len(done) == 2 and not failed
        assert sorted(os.listdir(tmp)) == ["doc-1.txt", "doc-2.txt", "keep.md"]

        open(os.path.join(tmp, "dup.txt"), "w").close()
        try:
            plan_renames(tmp, re.compile(r"^(doc-1|dup)"), "same")
        except RenameError:
            pass
        else:
            raise AssertionError("collision was not refused")

        try:
            plan_renames(tmp, re.compile(r"^keep\.md$"), "doc-2.txt")
        except RenameError:
            pass
        else:
            raise AssertionError("existing target was not refused")
        assert plan_renames(tmp, re.compile(r"zzz"), "x") == []
    print("self-test OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory", nargs="?", help="directory whose files are renamed")
    ap.add_argument("pattern", nargs="?", help="Python regular expression matched against each file name")
    ap.add_argument("replacement", nargs="?", help="replacement string; backreferences like \\1 work")
    ap.add_argument("--apply", action="store_true", help="actually rename (default: dry run)")
    ap.add_argument("--self-test", action="store_true", help="run offline self tests")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.directory or not args.pattern or args.replacement is None:
        ap.error("directory, pattern and replacement are required")
    if not os.path.isdir(args.directory):
        print(f"batch-rename: not a directory: {args.directory}", file=sys.stderr)
        return 2
    try:
        regex = re.compile(args.pattern)
    except re.error as exc:
        print(f"batch-rename: bad regex: {exc}", file=sys.stderr)
        return 2

    try:
        plans = plan_renames(args.directory, regex, args.replacement)
    except RenameError as exc:
        print(f"batch-rename: refusing to rename:\n{exc}", file=sys.stderr)
        return 2

    if not plans:
        print("nothing to rename")
        return 0
    verb = "renamed" if args.apply else "would rename"
    for old_name, new_name in plans:
        print(f"{verb}: {old_name} -> {new_name}")
    if not args.apply:
        print(f"\n{len(plans)} file(s) planned; dry run, use --apply to rename")
        return 0

    done, failed = apply_renames(args.directory, plans)
    print(f"\n{len(done)} renamed, {len(failed)} failed")
    for old_name, new_name, error in failed:
        print(f"  ! {old_name} -> {new_name}: {error}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
