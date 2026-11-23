#!/usr/bin/env python3
"""Offline password strength audit: length, classes, patterns, entropy."""

import argparse
import json
import math
import os
import re
import sys

COMMON = {
    "password", "123456", "12345678", "123456789", "qwerty", "qwerty123",
    "letmein", "admin", "welcome", "iloveyou", "dragon", "monkey", "abc123",
    "111111", "000000", "password1", "sunshine", "princess", "football",
}
SEQUENCES = ("abcdefghijklmnopqrstuvwxyz", "0123456789", "qwertyuiop",
             "asdfghjkl", "zxcvbnm")


def repeated_block(pw):
    for size in range(1, len(pw) // 2 + 1):
        if len(pw) % size == 0 and pw == pw[:size] * (len(pw) // size):
            return size
    return 0


def has_sequence(pw):
    for seq in SEQUENCES:
        for idx in range(len(seq) - 3):
            chunk = seq[idx:idx + 4]
            if chunk in pw or chunk[::-1] in pw:
                return True
    return False


def analyze(pw, min_length):
    has_lower = any(c.islower() for c in pw)
    has_upper = any(c.isupper() for c in pw)
    has_digit = any(c.isdigit() for c in pw)
    has_symbol = any(not c.isalnum() for c in pw)
    pool = (26 if has_lower else 0) + (26 if has_upper else 0) + \
           (10 if has_digit else 0) + (33 if has_symbol else 0)
    entropy = round(len(pw) * math.log2(pool), 1) if pool else 0.0

    issues = []
    low = pw.lower()
    if len(pw) < min_length:
        issues.append("shorter than %d" % min_length)
    if not (has_lower and has_upper and has_digit and has_symbol):
        issues.append("missing character classes")
    if low in COMMON or any(word in low for word in COMMON if len(word) >= 5):
        issues.append("common password word")
    block = repeated_block(pw)
    if block and len(pw) // block >= 2:
        issues.append("repeated block of %d chars" % block)
    if re.search(r"(.)\1{2,}", pw):
        issues.append("three or more repeated characters")
    if has_sequence(low):
        issues.append("sequential keyboard/alphabet run")
    score = 100
    score -= max(0, min_length - len(pw)) * 10
    score -= (4 - sum((has_lower, has_upper, has_digit, has_symbol))) * 12
    if "common password word" in issues:
        score -= 35
    if block:
        score -= 25
    if "three or more repeated characters" in issues:
        score -= 15
    if "sequential keyboard/alphabet run" in issues:
        score -= 10
    if entropy < 40:
        score -= 15
    score = max(0, min(100, score))
    if score < 30:
        rating = "weak"
    elif score < 55:
        rating = "fair"
    elif score < 75:
        rating = "good"
    else:
        rating = "strong"
    return {
        "length": len(pw),
        "classes": {"lower": has_lower, "upper": has_upper,
                    "digit": has_digit, "symbol": has_symbol},
        "class_count": sum((has_lower, has_upper, has_digit, has_symbol)),
        "entropy_bits": entropy,
        "score": score,
        "rating": rating,
        "issues": issues,
    }


def load_passwords(path):
    if path:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return [line.rstrip("\r\n") for line in fh if line.strip()]
    data = sys.stdin.read()
    return [line for line in data.splitlines() if line.strip()]


def self_test():
    import subprocess
    import tempfile

    script = os.path.abspath(__file__)
    samples = ["letmein", "abcabcabcabc", "Tr0ub4dor&3xK9!qZ", "aaaaaa123"]
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "candidates.txt")
        with open(src, "w", encoding="utf-8") as fh:
            fh.write("\n".join(samples) + "\n")
        result = subprocess.run(
            [sys.executable, script, "--file", src, "--json"],
            capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["count"] == 4
        rows = report["results"]
        assert rows[0]["rating"] == "weak", rows[0]
        assert any("repeated block" in i for i in rows[1]["issues"]), rows[1]
        assert rows[2]["rating"] == "strong", rows[2]
        for secret in samples:
            assert secret not in result.stdout
        empty = subprocess.run([sys.executable, script, "--json"],
                               input="", capture_output=True, text=True)
        assert empty.returncode == 2
    print("self-test: PASS")


def main():
    ap = argparse.ArgumentParser(
        description="Audit password candidates locally. Passwords are never echoed.")
    ap.add_argument("--file", help="read candidates one per line (default: stdin)")
    ap.add_argument("--min-length", type=int, default=8, help="policy minimum (default: 8)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--self-test", action="store_true", help="run built-in smoke test")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.min_length < 1:
        ap.error("--min-length must be positive")
    try:
        passwords = load_passwords(args.file)
    except OSError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    if not passwords:
        print("error: no password candidates supplied", file=sys.stderr)
        return 2
    results = [analyze(pw, args.min_length) for pw in passwords]
    if args.json:
        print(json.dumps({"min_length": args.min_length,
                          "count": len(results), "results": results}, indent=2))
    else:
        print("%-5s %-4s %-4s %-10s %-6s %-7s %s" %
              ("#", "len", "cls", "entropy", "score", "rating", "issues"))
        for idx, row in enumerate(results, 1):
            print("%-5d %-4d %-4d %-10.1f %-6d %-7s %s" %
                  (idx, row["length"], row["class_count"], row["entropy_bits"],
                   row["score"], row["rating"], ", ".join(row["issues"]) or "-"))
        weak = sum(1 for row in results if row["rating"] == "weak")
        print("\n%d candidate(s), %d weak" % (len(results), weak))
    return 0


if __name__ == "__main__":
    sys.exit(main())
