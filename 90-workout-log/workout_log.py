#!/usr/bin/env python3
"""Log strength sets and report weekly training volume."""

import argparse
import io
import json
import os
import sys
import tempfile
from datetime import date, timedelta

DEFAULT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workouts.json")


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return {"workouts": []}
    except (OSError, ValueError) as exc:
        sys.exit(f"error: cannot read {path}: {exc}")
    raw = data.get("workouts") if isinstance(data, dict) else None
    if not isinstance(raw, list):
        sys.exit(f"error: {path} must contain an object with a 'workouts' list")
    entries = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        exercise = str(item.get("exercise", "")).strip()
        try:
            day = date.fromisoformat(str(item["date"]))
            sets = int(item["sets"])
            reps = int(item["reps"])
            weight = float(item["weight"])
        except (KeyError, TypeError, ValueError):
            continue
        if not exercise or sets < 1 or reps < 1 or weight < 0:
            continue
        entries.append({
            "date": day.isoformat(),
            "exercise": exercise,
            "sets": sets,
            "reps": reps,
            "weight": round(weight, 2),
        })
    return {"workouts": entries}


def save(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def monday_of(day):
    return day - timedelta(days=day.weekday())


def volume(entry):
    return entry["sets"] * entry["reps"] * entry["weight"]


def log_entry(data, exercise, sets, reps, weight, when=None):
    exercise = exercise.strip()
    if not exercise:
        raise ValueError("exercise must not be empty")
    if sets < 1 or reps < 1:
        raise ValueError("sets and reps must be at least 1")
    if weight < 0:
        raise ValueError("weight must not be negative")
    entry = {
        "date": (when or date.today()).isoformat(),
        "exercise": exercise,
        "sets": int(sets),
        "reps": int(reps),
        "weight": round(float(weight), 2),
    }
    data["workouts"].append(entry)
    return entry


def week_stats(data, week):
    end = week + timedelta(days=7)
    entries = []
    for entry in data["workouts"]:
        day = date.fromisoformat(entry["date"])
        if week <= day < end:
            entries.append(entry)
    totals = {}
    for entry in entries:
        bucket = totals.setdefault(
            entry["exercise"], {"sets": 0, "reps": 0, "volume": 0.0}
        )
        bucket["sets"] += entry["sets"]
        bucket["reps"] += entry["sets"] * entry["reps"]
        bucket["volume"] += volume(entry)
    return entries, totals


def fmt_num(value):
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.1f}"


def show_stats(data, week, out=sys.stdout):
    entries, totals = week_stats(data, week)
    out.write(f"Week of {week.isoformat()}\n")
    if not entries:
        out.write("no workouts logged for this week\n")
        return
    out.write(f"{'exercise':<20} {'sets':>5} {'reps':>6} {'volume':>10}\n")
    for name in sorted(totals, key=lambda key: (-totals[key]["volume"], key)):
        bucket = totals[name]
        out.write(
            f"{name:<20} {bucket['sets']:>5} {bucket['reps']:>6}"
            f" {fmt_num(bucket['volume']):>10}\n"
        )
    total_volume = sum(bucket["volume"] for bucket in totals.values())
    total_sets = sum(bucket["sets"] for bucket in totals.values())
    total_reps = sum(bucket["reps"] for bucket in totals.values())
    out.write(f"{'total':<20} {total_sets:>5} {total_reps:>6} {fmt_num(total_volume):>10}\n")


def show_log(data, limit=10, out=sys.stdout):
    items = list(enumerate(data["workouts"]))
    items.sort(key=lambda pair: (pair[1]["date"], pair[0]))
    items.reverse()
    if not items:
        out.write("no workouts logged\n")
        return
    for _, entry in items[:limit]:
        out.write(
            f"{entry['date']}  {entry['exercise']:<16} {entry['sets']}x{entry['reps']}"
            f" @ {fmt_num(entry['weight'])}  vol {fmt_num(volume(entry))}\n"
        )


def positive(value):
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer")
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def weight_type(value):
    try:
        weight = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("weight must be a number")
    if weight < 0:
        raise argparse.ArgumentTypeError("weight must not be negative")
    return round(weight, 2)


def date_type(value):
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError("date must be YYYY-MM-DD")
    if parsed.isoformat() != value:
        raise argparse.ArgumentTypeError("date must be YYYY-MM-DD")
    return parsed


def self_test():
    assert monday_of(date(2026, 11, 25)) == date(2026, 11, 23)
    assert monday_of(date(2026, 11, 23)) == date(2026, 11, 23)
    assert fmt_num(100.0) == "100"
    assert fmt_num(12.5) == "12.5"

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "workouts.json")
        data = load(path)
        log_entry(data, "squat", 5, 5, 100, date(2026, 11, 23))
        log_entry(data, "squat", 3, 5, 110, date(2026, 11, 24))
        log_entry(data, "bench", 3, 8, 60, date(2026, 11, 25))
        log_entry(data, "row", 3, 10, 40, date(2026, 11, 30))
        save(path, data)
        loaded = load(path)
        assert len(loaded["workouts"]) == 4

        entries, totals = week_stats(loaded, date(2026, 11, 23))
        assert len(entries) == 3
        assert totals["squat"]["sets"] == 8
        assert totals["squat"]["reps"] == 40
        assert abs(totals["squat"]["volume"] - 4150) < 0.01
        total = sum(bucket["volume"] for bucket in totals.values())
        assert abs(total - 5590) < 0.01

        buffer = io.StringIO()
        show_stats(loaded, date(2026, 11, 23), buffer)
        report = buffer.getvalue()
        assert "squat" in report and "5590" in report

        next_entries, _ = week_stats(loaded, date(2026, 11, 30))
        assert len(next_entries) == 1

        buffer = io.StringIO()
        show_log(loaded, 2, buffer)
        assert len(buffer.getvalue().splitlines()) == 2

        for args in (("x", 0, 5, 10), ("x", 1, 0, 10), ("x", 1, 5, -1)):
            try:
                log_entry(data, *args)
            except ValueError:
                pass
            else:
                raise AssertionError(f"invalid entry accepted: {args}")
        empty = io.StringIO()
        show_stats({"workouts": []}, date(2026, 11, 23), empty)
        assert "no workouts" in empty.getvalue()
    print("self-test OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Log sets, reps, and weight; report weekly training volume.",
        epilog="Volume is sets x reps x weight per exercise. Weeks run Monday "
        "to Sunday. Exit codes: 0 success, 1 storage or input error, 2 usage "
        "error.",
    )
    ap.add_argument("--file", default=DEFAULT_FILE, help="workout JSON file")
    ap.add_argument("--self-test", action="store_true", help="run built-in checks")
    sub = ap.add_subparsers(dest="command", metavar="command")

    log_parser = sub.add_parser("log", help="record an exercise")
    log_parser.add_argument("exercise")
    log_parser.add_argument("--sets", type=positive, default=1)
    log_parser.add_argument("--reps", type=positive, required=True)
    log_parser.add_argument("--weight", type=weight_type, required=True)
    log_parser.add_argument("--date", type=date_type, default=None, metavar="YYYY-MM-DD")

    list_parser = sub.add_parser("list", help="recent entries, newest first")
    list_parser.add_argument("-n", "--limit", type=positive, default=10)

    stats_parser = sub.add_parser("stats", help="weekly volume by exercise")
    stats_parser.add_argument("--week", type=date_type, default=None, metavar="YYYY-MM-DD")

    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.command:
        ap.print_help()
        return 2

    data = load(args.file)
    try:
        if args.command == "log":
            entry = log_entry(data, args.exercise, args.sets, args.reps,
                              args.weight, args.date)
            save(args.file, data)
            print(
                f"logged {entry['exercise']} {entry['sets']}x{entry['reps']}"
                f" @ {fmt_num(entry['weight'])} on {entry['date']}"
            )
        elif args.command == "list":
            show_log(data, args.limit)
        elif args.command == "stats":
            show_stats(data, monday_of(args.week or date.today()))
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
