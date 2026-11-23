#!/usr/bin/env python3
"""Scan text files for common secret patterns; redact every match in output."""

import argparse
import json
import os
import re
import sys

PATTERNS = [
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), 0),
    ("aws_secret_key", re.compile(
        r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})"), 1),
    ("private_key", re.compile(
        r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY(?: BLOCK)?-----"), 0),
    ("github_token", re.compile(
        r"\b(?:ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{30,})\b"), 0),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), 0),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), 0),
    ("jwt", re.compile(
        r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"), 0),
    ("generic_secret", re.compile(
        r"(?i)\b(?:api[_-]?key|secret|token|password)\s*[:=]\s*"
        r"['\"]([A-Za-z0-9_\-./+=]{16,})['\"]"), 1),
]
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip",
            ".gz", ".bz2", ".xz", ".7z", ".tar", ".pyc", ".so", ".o", ".a",
            ".woff", ".woff2", ".ttf", ".mp3", ".mp4", ".mov", ".bin", ".iso"}


def redact(value):
    if len(value) <= 4:
        return "*" * len(value)
    if len(value) <= 8:
        return value[0] + "*" * (len(value) - 2) + value[-1]
    return value[:4] + "*" * (len(value) - 8) + value[-4:]


def scan_file(path, max_size):
    try:
        st = os.stat(path)
        if not os.path.isfile(path) or os.path.islink(path) or st.st_size > max_size:
            return []
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError:
        return []
    if b"\x00" in data[:8192]:
        return []
    text = data.decode("utf-8", errors="replace")
    findings = []
    for lineno, line in enumerate(text.splitlines(), 1):
        spans = set()
        for name, regex, group in PATTERNS:
            for match in regex.finditer(line):
                value = match.group(group)
                key = (match.start(group), match.end(group))
                if key in spans:
                    continue
                spans.add(key)
                findings.append({
                    "file": path,
                    "line": lineno,
                    "pattern": name,
                    "match": redact(value),
                    "length": len(value),
                })
    return findings


def iter_files(paths, excludes):
    for item in paths:
        if os.path.isfile(item):
            yield item
        elif os.path.isdir(item):
            for dirpath, dirnames, filenames in os.walk(item):
                dirnames[:] = sorted(d for d in dirnames
                                     if d not in SKIP_DIRS and d not in excludes)
                for name in sorted(filenames):
                    if os.path.splitext(name)[1].lower() in SKIP_EXT:
                        continue
                    yield os.path.join(dirpath, name)
        else:
            raise FileNotFoundError(item)


def scan(paths, excludes, max_size):
    findings = []
    files = 0
    for path in iter_files(paths, excludes):
        files += 1
        findings.extend(scan_file(path, max_size))
    return files, findings


def self_test():
    import subprocess
    import tempfile

    script = os.path.abspath(__file__)
    fake_aws = "AKIA" + "IOSFODNN7" + "EXAMPLE"
    fake_key = "-----BEGIN " + "OPENSSH PRIVATE KEY-----"
    with tempfile.TemporaryDirectory() as tmp:
        tree = os.path.join(tmp, "tree")
        clean_dir = os.path.join(tmp, "clean")
        os.makedirs(tree)
        os.makedirs(clean_dir)
        with open(os.path.join(tree, "creds.txt"), "w", encoding="utf-8") as fh:
            fh.write("key = %s\n" % fake_aws)
        with open(os.path.join(tree, "id_key"), "w", encoding="utf-8") as fh:
            fh.write(fake_key + "\n")
        with open(os.path.join(clean_dir, "notes.txt"), "w", encoding="utf-8") as fh:
            fh.write("nothing sensitive here\n")
        result = subprocess.run([sys.executable, script, "--json", tree],
                                capture_output=True, text=True)
        assert result.returncode == 1, result.stdout + result.stderr
        report = json.loads(result.stdout)
        names = {row["pattern"] for row in report["findings"]}
        assert {"aws_access_key", "private_key"} <= names, names
        assert fake_aws not in result.stdout, "full secret leaked"
        assert "AKIA************MPLE" in result.stdout
        assert report["scanned_files"] == 2, report["scanned_files"]
        result = subprocess.run([sys.executable, script, "--json", clean_dir],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stdout
        assert json.loads(result.stdout)["count"] == 0
        result = subprocess.run([sys.executable, script, os.path.join(tmp, "missing")],
                                capture_output=True, text=True)
        assert result.returncode == 2
    print("self-test: PASS")


def main():
    ap = argparse.ArgumentParser(
        description="Scan files for AWS keys, private-key headers, and tokens; "
                    "redact matches in output.")
    ap.add_argument("paths", nargs="*", help="files/directories (default: .)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--exclude", action="append", default=[],
                    help="extra directory name to skip (repeatable)")
    ap.add_argument("--max-size", type=int, default=2_000_000,
                    help="skip files larger than this many bytes")
    ap.add_argument("--self-test", action="store_true", help="run built-in smoke test")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.max_size < 1:
        ap.error("--max-size must be positive")
    try:
        files, findings = scan(args.paths or ["."], set(args.exclude), args.max_size)
    except OSError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    counts = {}
    for row in findings:
        counts[row["pattern"]] = counts.get(row["pattern"], 0) + 1
    if args.json:
        print(json.dumps({"scanned_files": files, "count": len(findings),
                          "counts": counts, "findings": findings}, indent=2))
    else:
        for row in findings:
            print("%s:%d: [%s] %s" % (row["file"], row["line"],
                                      row["pattern"], row["match"]))
        print("\n%d finding(s) in %d scanned file(s)" % (len(findings), files))
        if findings:
            print("matches are redacted; review the source files directly")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
