#!/usr/bin/env python3
"""Run each project's smoke test. Scans NN-slug folders and prefers test.sh,
then test.py, then <main>.py --self-test.  Exits 1 on any failure."""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def command_for(path: str):
    files = sorted(os.listdir(path))
    if "test.sh" in files:
        return ["bash", os.path.join(path, "test.sh")]
    if "test.py" in files:
        return [sys.executable, os.path.join(path, "test.py")]
    for name in files:
        if name.endswith(".py"):
            full = os.path.join(path, name)
            try:
                text = open(full, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            if "__main__" in text:
                return [sys.executable, full, "--self-test"]
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--range", default="1-100")
    ap.add_argument("--timeout", type=float, default=20.0)
    a = ap.parse_args()
    lo, hi = map(int, a.range.split("-"))
    failed, passed, skipped = [], 0, []
    for name in sorted(os.listdir(ROOT)):
        m = re.match(r"^(\d{2,3})-[a-z0-9-]+$", name)
        if not m:
            continue
        num = int(m.group(1))
        if not (lo <= num <= hi):
            continue
        path = os.path.join(ROOT, name)
        if not os.path.isdir(path):
            continue
        cmd = command_for(path)
        if not cmd:
            skipped.append(name)
            continue
        try:
            res = subprocess.run(cmd, cwd=path, capture_output=True, text=True,
                                 timeout=a.timeout, errors="replace")
        except subprocess.TimeoutExpired:
            failed.append((name, "timeout"))
            continue
        if res.returncode == 0:
            passed += 1
        else:
            tail = (res.stderr or res.stdout).strip().splitlines()
            failed.append((name, tail[-1][:120] if tail else f"rc={res.returncode}"))
    print(f"passed {passed}, failed {len(failed)}, skipped {len(skipped)}")
    for name, why in failed:
        print(f"  FAIL {name}: {why}")
    for name in skipped:
        print(f"  SKIP {name}: no test found")
    return 1 if failed or skipped else 0


if __name__ == "__main__":
    sys.exit(main())
