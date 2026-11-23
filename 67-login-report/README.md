# 67 - login-report

Parse `last -F` output and count successful logins per user per calendar day.
Lines explicitly marked `failed`, plus optional `lastb -F` output, are counted
in a separate bucket. Boot records (`reboot`, `shutdown`) are ignored.

`--file` accepts saved output, so the parser is testable and works on captured
artifacts. Without it, the tool runs `last -F` itself.

## Usage

```sh
./login_report.py
./login_report.py --json
./login_report.py --failed          # adds lastb -F, if permitted
./login_report.py --file last.txt --json
```

Text output is a `USER DAY COUNT` table plus totals and, when present, a failed-
entries table. JSON report:

```json
{"source": "last -F", "logins": [{"user": "emre", "day": "2026-11-23", "count": 2}],
 "failed_logins": [], "total_logins": 2, "total_failed": 0, "records": 3,
 "users": ["emre"], "days": ["2026-11-23"], "notes": []}
```

`lastb` commonly requires root; that is reported as a note rather than a hard
failure. An empty login database is valid and exits 0.

## Exit codes

| code | meaning |
|------|---------|
| 0 | report produced (possibly empty) |
| 2 | input file or `last` command unavailable |

## Self-test

```sh
./login_report.py --self-test
```

Feeds a fixed `last -F` fixture covering multiple users/days, a boot record,
and a failed entry; checks counts, day formatting, and the missing-file error.
