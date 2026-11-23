#!/usr/bin/env python3
"""Summarize login records from `last -F` (or lastb) by user and day."""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from collections import Counter

MONTHS = {name: idx for idx, name in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
SKIP_USERS = {"reboot", "shutdown", "wtmp", "wtmpdb", "runlevel", "system"}


def run_last(command):
    try:
        proc = subprocess.run(command, capture_output=True, text=True,
                              timeout=15, env={**os.environ, "LC_ALL": "C"})
    except FileNotFoundError:
        return None, "%s not installed" % command[0]
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)
    if proc.returncode != 0:
        text = (proc.stderr or proc.stdout).strip()
        return None, text.splitlines()[0] if text else "exit %d" % proc.returncode
    return proc.stdout, None


def parse_year(token, month_idx, tokens):
    if len(tokens) > month_idx + 3 and re.fullmatch(r"\d{4}", tokens[month_idx + 3]):
        return int(tokens[month_idx + 3])
    return datetime.date.today().year


def parse_line(line):
    tokens = line.split()
    if len(tokens) < 5 or tokens[0] in SKIP_USERS or tokens[1] == "begins":
        return None
    month_idx = next((i for i, tok in enumerate(tokens) if tok in MONTHS), None)
    if month_idx is None or month_idx < 1:
        return None
    try:
        day = int(tokens[month_idx + 1])
        clock = tokens[month_idx + 2].split(":")
        if len(clock) != 3:
            return None
        hour, minute, second = (int(part) for part in clock)
        year = parse_year(tokens[month_idx + 2], month_idx, tokens)
        date = datetime.date(year, MONTHS[tokens[month_idx]], day)
    except (ValueError, IndexError, KeyError):
        return None
    return {
        "user": tokens[0],
        "day": date.isoformat(),
        "time": "%02d:%02d:%02d" % (hour, minute, second),
        "failed": "failed" in line.lower(),
    }


def summarize(text, force_failed=False):
    logins = Counter()
    failed = Counter()
    records = 0
    for line in text.splitlines():
        row = parse_line(line)
        if not row:
            continue
        records += 1
        is_failed = force_failed or row["failed"]
        bucket = failed if is_failed else logins
        bucket[(row["user"], row["day"])] += 1
    login_rows = [{"user": user, "day": day, "count": count}
                  for (user, day), count in sorted(logins.items())]
    failed_rows = [{"user": user, "day": day, "count": count}
                   for (user, day), count in sorted(failed.items())]
    return {
        "logins": login_rows,
        "failed_logins": failed_rows,
        "total_logins": sum(logins.values()),
        "total_failed": sum(failed.values()),
        "records": records,
        "users": sorted({user for user, _ in logins}),
        "days": sorted({day for _, day in logins}),
    }


def self_test():
    import subprocess
    import tempfile

    script = os.path.abspath(__file__)
    fixture = """\
emre     pts/0        10.0.0.5         Mon Nov 23 21:06:00 2026   still logged in
emre     pts/1        10.0.0.6         Mon Nov 23 09:00:00 2026 - Mon Nov 23 10:00:00 2026  (01:00)
alice    tty1                          Tue Nov 24 08:00:00 2026 - Tue Nov 24 09:00:00 2026  (01:00)
reboot   system boot  6.8.0             Mon Nov 23 08:00:00 2026   still running
mallory  ssh:notty    10.9.9.9         Mon Nov 23 22:00:00 2026 - Mon Nov 23 22:00:01 2026  (00:01) failed
"""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "last.txt")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(fixture)
        result = subprocess.run([sys.executable, script, "--file", path, "--json"],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["total_logins"] == 3, report
        assert report["total_failed"] == 1, report
        by_user = {row["user"]: row["count"] for row in report["logins"]}
        assert by_user == {"emre": 2, "alice": 1}, by_user
        assert {row["user"] for row in report["failed_logins"]} == {"mallory"}
        assert "reboot" not in by_user
        assert all(len(row["day"]) == 10 for row in report["logins"])
        result = subprocess.run([sys.executable, script, "--file",
                                 os.path.join(tmp, "missing.txt")],
                                capture_output=True, text=True)
        assert result.returncode == 2
    print("self-test: PASS")


def main():
    ap = argparse.ArgumentParser(
        description="Count logins per user/day from last -F output.")
    ap.add_argument("--file", help="read saved `last -F` output instead of running it")
    ap.add_argument("--failed", action="store_true",
                    help="also query lastb -F for failed logins")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--self-test", action="store_true", help="run built-in smoke test")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0

    notes = []
    if args.file:
        try:
            with open(args.file, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError as exc:
            print("error: %s" % exc, file=sys.stderr)
            return 2
        source = args.file
    else:
        text, error = run_last(["last", "-F"])
        if text is None:
            print("error: cannot read login records: %s" % error, file=sys.stderr)
            return 2
        source = "last -F"

    report = summarize(text)
    if args.failed:
        failed_text, error = run_last(["lastb", "-F"])
        if failed_text is None:
            notes.append("failed login records unavailable: %s" % error)
        else:
            failed_report = summarize(failed_text, force_failed=True)
            merged = Counter()
            for row in report["failed_logins"] + failed_report["failed_logins"]:
                merged[(row["user"], row["day"])] += row["count"]
            report["failed_logins"] = [
                {"user": user, "day": day, "count": count}
                for (user, day), count in sorted(merged.items())]
            report["total_failed"] = sum(merged.values())

    report["source"] = source
    report["notes"] = notes
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("logins per user/day (source: %s)" % source)
        print("%-16s %-12s %s" % ("USER", "DAY", "COUNT"))
        for row in report["logins"]:
            print("%-16.16s %-12s %d" % (row["user"], row["day"], row["count"]))
        print("\n%d login(s), %d user(s), %d day(s)" %
              (report["total_logins"], len(report["users"]), len(report["days"])))
        if report["failed_logins"]:
            print("\nfailed entries:")
            print("%-16s %-12s %s" % ("USER", "DAY", "COUNT"))
            for row in report["failed_logins"]:
                print("%-16.16s %-12s %d" % (row["user"], row["day"], row["count"]))
            print("%d failed entr(ies)" % report["total_failed"])
        elif not notes:
            print("no failed entries present in the source")
        for note in notes:
            print("note: %s" % note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
