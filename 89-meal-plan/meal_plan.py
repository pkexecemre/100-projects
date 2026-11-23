#!/usr/bin/env python3
"""Plan weekly meals in a JSON calendar."""

import argparse
import io
import json
import os
import sys
import tempfile
from datetime import date, timedelta

DEFAULT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meal-plan.json")
SLOTS = ["breakfast", "lunch", "dinner", "snack"]
WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
ALIASES = {
    "monday": "mon",
    "tuesday": "tue",
    "wednesday": "wed",
    "thursday": "thu",
    "friday": "fri",
    "saturday": "sat",
    "sunday": "sun",
}


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return {"meals": {}}
    except (OSError, ValueError) as exc:
        sys.exit(f"error: cannot read {path}: {exc}")
    raw = data.get("meals") if isinstance(data, dict) else None
    if not isinstance(raw, dict):
        sys.exit(f"error: {path} must contain an object with a 'meals' mapping")
    meals = {}
    for day, slots in raw.items():
        if not isinstance(slots, dict):
            continue
        try:
            date.fromisoformat(day)
        except (TypeError, ValueError):
            continue
        clean = {}
        for slot, dish in slots.items():
            if slot in SLOTS and isinstance(dish, str) and dish.strip():
                clean[slot] = dish.strip()
        if clean:
            meals[day] = clean
    return {"meals": meals}


def save(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)


def monday_of(day):
    return day - timedelta(days=day.weekday())


def parse_day(value, week):
    key = value.strip().lower()
    key = ALIASES.get(key, key)
    if key in WEEKDAYS:
        return week + timedelta(days=WEEKDAYS.index(key))
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        raise ValueError(f"unknown day: {value} (use mon..sun or YYYY-MM-DD)")


def parse_slot(value):
    slot = value.strip().lower()
    if slot not in SLOTS:
        raise ValueError(f"unknown slot: {value} (use {', '.join(SLOTS)})")
    return slot


def set_meal(data, day, slot, dish):
    dish = dish.strip()
    if not dish:
        raise ValueError("dish must not be empty")
    data["meals"].setdefault(day.isoformat(), {})[slot] = dish


def remove_meal(data, day, slot):
    stamp = day.isoformat()
    slots = data["meals"].get(stamp)
    if not slots or slot not in slots:
        return False
    del slots[slot]
    if not slots:
        del data["meals"][stamp]
    return True


def show_week(data, week, today=None, out=sys.stdout):
    today = today or date.today()
    out.write(f"Week of {week.isoformat()}")
    if week <= today < week + timedelta(days=7):
        out.write(" (current week)")
    out.write("\n")
    for offset, name in enumerate(WEEKDAYS):
        day = week + timedelta(days=offset)
        marker = "  * today" if day == today else ""
        out.write(f"{name} {day.isoformat()}{marker}\n")
        slots = data["meals"].get(day.isoformat(), {})
        for slot in SLOTS:
            out.write(f"  {slot:<9} {slots.get(slot, '-')}\n")


def date_type(value):
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError("date must be YYYY-MM-DD")
    if parsed.isoformat() != value:
        raise argparse.ArgumentTypeError("date must be YYYY-MM-DD")
    return parsed


def self_test():
    today = date(2026, 11, 23)
    week = monday_of(today)
    assert week == today
    assert monday_of(date(2026, 11, 29)) == today
    assert parse_day("fri", week) == date(2026, 11, 27)
    assert parse_day("Monday", week) == today
    assert parse_day("2026-12-01", week) == date(2026, 12, 1)
    assert parse_slot("Dinner") == "dinner"
    for bad in ("brunch", "2026-13-01"):
        try:
            parse_slot(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid slot accepted: {bad}")

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "meal-plan.json")
        data = load(path)
        set_meal(data, parse_day("mon", week), "dinner", "Pasta")
        set_meal(data, parse_day("wed", week), "lunch", "Soup")
        save(path, data)
        loaded = load(path)
        assert loaded["meals"]["2026-11-23"]["dinner"] == "Pasta"
        buffer = io.StringIO()
        show_week(loaded, week, today, buffer)
        report = buffer.getvalue()
        assert "Pasta" in report and "Soup" in report and "* today" in report
        assert remove_meal(loaded, date(2026, 11, 25), "lunch")
        assert not remove_meal(loaded, date(2026, 11, 25), "lunch")
        assert "2026-11-25" not in loaded["meals"]
        try:
            set_meal(loaded, week, "dinner", "   ")
        except ValueError:
            pass
        else:
            raise AssertionError("empty dish accepted")
    print("self-test OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Plan breakfast, lunch, dinner, and snacks for the week.",
        epilog="Days are mon..sun (or full names) resolved inside a week, or "
        "an explicit YYYY-MM-DD. Exit codes: 0 success, 1 bad meal or storage "
        "error, 2 usage error.",
    )
    ap.add_argument("--file", default=DEFAULT_FILE, help="meal plan JSON file")
    ap.add_argument("--self-test", action="store_true", help="run built-in checks")
    sub = ap.add_subparsers(dest="command", metavar="command")

    add_parser = sub.add_parser("add", help="set one meal")
    add_parser.add_argument("day")
    add_parser.add_argument("slot")
    add_parser.add_argument("dish", nargs="+")
    add_parser.add_argument("--week", type=date_type, default=None, metavar="YYYY-MM-DD")

    show_parser = sub.add_parser("show", help="show a week")
    show_parser.add_argument("--week", type=date_type, default=None, metavar="YYYY-MM-DD")

    remove_parser = sub.add_parser("remove", help="clear one meal")
    remove_parser.add_argument("day")
    remove_parser.add_argument("slot")
    remove_parser.add_argument("--week", type=date_type, default=None, metavar="YYYY-MM-DD")

    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.command:
        ap.print_help()
        return 2

    data = load(args.file)
    try:
        if args.command == "show":
            week = monday_of(args.week or date.today())
            show_week(data, week)
            return 0
        week = monday_of(args.week or date.today())
        day = parse_day(args.day, week)
        slot = parse_slot(args.slot)
        if args.command == "add":
            set_meal(data, day, slot, " ".join(args.dish))
            save(args.file, data)
            print(f"planned {slot} on {day.isoformat()}: {' '.join(args.dish).strip()}")
        elif args.command == "remove":
            if not remove_meal(data, day, slot):
                print(f"error: no {slot} planned on {day.isoformat()}", file=sys.stderr)
                return 1
            save(args.file, data)
            print(f"removed {slot} on {day.isoformat()}")
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
