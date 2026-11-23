#!/usr/bin/env python3
"""Line-oriented diff using a longest-common-subsequence table."""

import argparse
import sys

MAX_CELLS = 16_000_000


def read_lines(path):
    if path == "-":
        return sys.stdin.read().splitlines()
    with open(path, encoding="utf-8") as handle:
        return handle.read().splitlines()


def lcs_table(old, new):
    """Build the suffix LCS length table (rows=old, cols=new)."""
    rows, cols = len(old), len(new)
    table = [[0] * (cols + 1) for _ in range(rows + 1)]
    for i in range(rows - 1, -1, -1):
        row, below = table[i], table[i + 1]
        for j in range(cols - 1, -1, -1):
            if old[i] == new[j]:
                row[j] = below[j + 1] + 1
            else:
                row[j] = below[j] if below[j] >= row[j + 1] else row[j + 1]
    return table


def diff_lines(old, new):
    """Return [(marker, line)] where marker is ' ', '-', or '+'."""
    if len(old) * len(new) > MAX_CELLS:
        raise ValueError("input too large for the LCS table; split the files")
    table = lcs_table(old, new)
    result = []
    i = j = 0
    while i < len(old) and j < len(new):
        if old[i] == new[j]:
            result.append((" ", old[i]))
            i += 1
            j += 1
        elif table[i + 1][j] >= table[i][j + 1]:
            result.append(("-", old[i]))
            i += 1
        else:
            result.append(("+", new[j]))
            j += 1
    result.extend(("-", line) for line in old[i:])
    result.extend(("+", line) for line in new[j:])
    return result


def self_test():
    old = ["one", "two", "three", "four"]
    new = ["one", "two A", "three", "four", "five"]
    ops = diff_lines(old, new)
    assert [op for op, _ in ops] == [" ", "-", "+", " ", " ", "+"]
    assert ("-", "two") in ops and ("+", "two A") in ops and ("+", "five") in ops
    assert diff_lines([], []) == []
    assert diff_lines(["a"], []) == [("-", "a")]
    assert diff_lines([], ["a"]) == [("+", "a")]
    assert diff_lines(["same"], ["same"]) == [(" ", "same")]

    import os
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        first = os.path.join(tmp, "a.txt")
        second = os.path.join(tmp, "b.txt")
        with open(first, "w", encoding="utf-8") as handle:
            handle.write("a\nb\n")
        with open(second, "w", encoding="utf-8") as handle:
            handle.write("a\nc\n")
        same = subprocess.run([sys.executable, __file__, first, first],
                              capture_output=True, text=True)
        differ = subprocess.run([sys.executable, __file__, first, second],
                                capture_output=True, text=True)
        stat = subprocess.run([sys.executable, __file__, "--stat", first, second],
                              capture_output=True, text=True)
    assert same.returncode == 0 and differ.returncode == 1 and stat.returncode == 1
    assert "- b" in differ.stdout and "+ c" in differ.stdout
    assert "1 addition" in stat.stdout and "1 deletion" in stat.stdout
    print("self-test: 12 checks passed")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Diff two files line by line with + and - markers.")
    parser.add_argument("old", nargs="?", help="original file (or - for stdin)")
    parser.add_argument("new", nargs="?", help="new file (or - for stdin)")
    parser.add_argument("--stat", action="store_true",
                        help="print only addition/deletion counts")
    parser.add_argument("--self-test", action="store_true",
                        help="run offline checks and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        self_test()
        return 0
    if args.old is None or args.new is None:
        parser.error("two input files are required")
    if args.old == "-" and args.new == "-":
        parser.error("only one input may be stdin")

    try:
        old = read_lines(args.old)
        new = read_lines(args.new)
        ops = diff_lines(old, new)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print("line-diff: error: %s" % exc, file=sys.stderr)
        return 2

    added = sum(1 for op, _ in ops if op == "+")
    removed = sum(1 for op, _ in ops if op == "-")
    if args.stat:
        print("%d addition%s, %d deletion%s" % (
            added, "" if added == 1 else "s",
            removed, "" if removed == 1 else "s"))
    else:
        for marker, line in ops:
            print("%s %s" % (marker, line))
    return 1 if added or removed else 0


if __name__ == "__main__":
    sys.exit(main())
