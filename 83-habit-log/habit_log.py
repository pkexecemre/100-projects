#!/usr/bin/env python3
"""Track daily habits in a JSON file and report streaks."""

import argparse
import io
import json
import os
import sys
import tempfile
from datetime import date, timedelta

DEFAULT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "habits.json")


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return {"habits": {}}
    except (OSError, ValueError) as exc:
        sys.exit(f"error: cannot read {path}: {exc}")
    habits = data.get("habits") if isinstance(data, dict) else None
    if not isinstance(habits, dict):
        sys.exit(f"error: {path} must contain an object with a 'habits' mapping")
    clean = {}
    for name, days in habits.items():
        if isinstance(days, list):
            clean[str(name)] = sorted({day for day in days if isinstance(day, str)})
    return {"habits": clean}


def save(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)


def add_checkin(data, name, today):
    days = data["habits"].setdefault(name, [])
    stamp = today.isoformat()
    if stamp in days:
        return False
    days.append(stamp)
    days.sort()
    return True


def parse_days(days):
    parsed = set()
    for value in days:
        try:
            parsed.add(date.fromisoformat(value))
        except (TypeError, ValueError):
            continue
    return parsed


def current_streak(days, today):
    """Consecutive days ending today, or yesterday when today is unlogged."""
    known = parse_days(days)
    cursor = today if today in known else today - timedelta(days=1)
    streak = 0
    while cursor in known:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def best_streak(days):
    ordered = sorted(parse_days(days))
    best = 0
    run = 0
    previous = None
    for day in ordered:
        run = run + 1 if previous and (day - previous).days == 1 else 1
        best = max(best, run)
        previous = day
    return best


def last_seven(days, today):
    known = parse_days(days)
    start = today - timedelta(days=6)
    return sum(1 for offset in range(7) if start + timedelta(days=offset) in known)


def show_stats(data, today, out=sys.stdout):
    habits = data["habits"]
    if not habits:
        out.write("no habits logged yet\n")
        return
    rows = []
    for name in sorted(habits):
        days = habits[name]
        rows.append((
            name,
            current_streak(days, today),
            best_streak(days),
            len(parse_days(days)),
            last_seven(days, today),
        ))
    width = max(len(row[0]) for row in rows)
    out.write(f"{'habit':<{width}}  streak  best  total  last7\n")
    for name, streak, best, total, week in rows:
        out.write(f"{name:<{width}}  {streak:>6}  {best:>4}  {total:>5}  {week:>5}\n")


def self_test():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "habits.json")
        data = load(path)
        today = date(2026, 11, 23)
        assert add_checkin(data, "read", today - timedelta(days=2))
        assert add_checkin(data, "read", today - timedelta(days=1))
        assert add_checkin(data, "read", today)
        assert not add_checkin(data, "read", today)
        save(path, data)
        loaded = load(path)
        days = loaded["habits"]["read"]
        assert days == ["2026-11-21", "2026-11-22", "2026-11-23"]
        assert current_streak(days, today) == 3
        assert best_streak(days) == 3
        assert last_seven(days, today) == 3
        gapped = ["2026-11-19", "2026-11-20", "2026-11-23"]
        assert current_streak(gapped, today) == 1
        assert best_streak(gapped) == 2
        assert current_streak(["2026-11-21", "2026-11-22"], today) == 2
        assert current_streak([], today) == 0
        buffer = io.StringIO()
        show_stats(loaded, today, buffer)
        report = buffer.getvalue()
        assert "read" in report and "3" in report
        empty = io.StringIO()
        show_stats({"habits": {}}, today, empty)
        assert empty.getvalue() == "no habits logged yet\n"
    print("self-test OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Check in daily habits and report streak statistics.",
        epilog="Streaks end today, or yesterday while today is still unlogged. "
        "Exit codes: 0 success, 1 storage or input error, 2 usage error.",
    )
    ap.add_argument("--file", default=DEFAULT_FILE, help="habits JSON file")
    ap.add_argument("--add", metavar="HABIT", help="check in HABIT for today")
    ap.add_argument("--stats", action="store_true", help="show streaks and totals")
    ap.add_argument("--self-test", action="store_true", help="run built-in checks")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.add is None and not args.stats:
        ap.print_help()
        return 2

    today = date.today()
    data = load(args.file)
    if args.add is not None:
        name = args.add.strip()
        if not name:
            print("error: habit name must not be empty", file=sys.stderr)
            return 1
        if add_checkin(data, name, today):
            save(args.file, data)
            print(f"checked in: {name} ({today.isoformat()})")
        else:
            print(f"already checked in today: {name}")
    if args.stats:
        show_stats(data, today)
    return 0


if __name__ == "__main__":
    sys.exit(main())
