#!/usr/bin/env python3
"""Explain a 5-field cron expression and preview its next run times."""

import argparse
import datetime
import sys

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
MONTH_FULL = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"]
DAYS = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
DAY_FULL = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

FIELDS = [
    ("minute", 0, 59, None),
    ("hour", 0, 23, None),
    ("day of month", 1, 31, None),
    ("month", 1, 12, MONTHS),
    ("day of week", 0, 7, DAYS),
]


def parse_value(token, lo, hi, names, label):
    if names and token.upper() in names:
        return lo + names.index(token.upper())
    try:
        value = int(token)
    except ValueError:
        raise ValueError(f"{label}: {token!r} is not a number")
    if not lo <= value <= hi:
        raise ValueError(f"{label}: {value} is outside {lo}-{hi}")
    return value


def parse_field(text, lo, hi, names, label):
    if not text:
        raise ValueError(f"{label}: empty field")
    values = set()
    for part in text.split(","):
        if not part:
            raise ValueError(f"{label}: empty list element")
        base, sep, step_text = part.partition("/")
        step = 1
        if sep:
            if not step_text.isdigit() or int(step_text) == 0:
                raise ValueError(f"{label}: bad step {step_text!r}")
            step = int(step_text)
        if base == "*":
            start, end = lo, hi
        elif "-" in base:
            left, _, right = base.partition("-")
            start = parse_value(left, lo, hi, names, label)
            end = parse_value(right, lo, hi, names, label)
            if start > end:
                raise ValueError(f"{label}: range {base!r} is reversed")
        else:
            start = parse_value(base, lo, hi, names, label)
            end = hi if sep else start
        values.update(range(start, end + 1, step))
    return values


def parse_cron(expr):
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError(f"expected 5 fields, got {len(parts)}")
    result = {}
    for (label, lo, hi, names), text in zip(FIELDS, parts):
        result[label] = parse_field(text, lo, hi, names, label)
    result["day of week"] = {0 if v == 7 else v for v in result["day of week"]}
    result["dom_star"] = parts[2] == "*"
    result["dow_star"] = parts[4] == "*"
    result["expr"] = parts
    return result


def compress(values):
    values = sorted(values)
    runs = []
    start = prev = values[0]
    for value in values[1:]:
        if value == prev + 1:
            prev = value
        else:
            runs.append((start, prev))
            start = prev = value
    runs.append((start, prev))
    pieces = []
    for a, b in runs:
        if a == b:
            pieces.append(str(a))
        elif b == a + 1:
            pieces.extend([str(a), str(b)])
        else:
            pieces.append(f"{a} through {b}")
    return ", ".join(pieces)


def compress_names(values, names, offset=0):
    runs, current = [], []
    for value in sorted(values):
        if current and value == current[-1] + 1:
            current.append(value)
        else:
            if current:
                runs.append(current)
            current = [value]
    if current:
        runs.append(current)
    pieces = []
    for run in runs:
        if len(run) == 1:
            pieces.append(names[run[0] - offset])
        elif len(run) == 2:
            pieces.extend(names[v - offset] for v in run)
        else:
            pieces.append(f"{names[run[0] - offset]} through {names[run[-1] - offset]}")
    return ", ".join(pieces)


def step_of(expr):
    base, sep, step = expr.partition("/")
    if not sep:
        return 1, None
    return int(step), base


def minute_phrase(expr, values):
    step, base = step_of(expr)
    if expr == "*":
        return "every minute"
    if base is not None:
        if base == "*":
            return f"every {step} minutes"
        return f"every {step} minutes from {min(values)} through {max(values)}"
    if len(values) == 1:
        return f"at minute {min(values)}"
    return f"at minutes {compress(values)}"


def hour_phrase(expr, values):
    step, base = step_of(expr)
    if expr == "*":
        return "of every hour"
    if base is not None:
        if base == "*":
            return f"every {step} hours"
        return f"every {step} hours from {min(values)} through {max(values)}"
    if len(values) == 1:
        return f"past hour {min(values):02d}"
    return f"past hours {compress(values)}"


def dom_phrase(expr, values):
    step, base = step_of(expr)
    if expr == "*":
        return ""
    if base is not None:
        if base == "*":
            return f"every {step} days of the month"
        return f"every {step} days from day {min(values)} through {max(values)} of the month"
    if len(values) == 1:
        return f"on day {min(values)} of the month"
    return f"on days {compress(values)} of the month"


def month_phrase(expr, values):
    step, base = step_of(expr)
    if expr == "*":
        return ""
    if base is not None and base == "*":
        return f"every {step} months"
    names = compress_names(values, MONTH_FULL, offset=1)
    return f"in {names}"


def dow_phrase(expr, values):
    step, base = step_of(expr)
    if expr == "*":
        return ""
    if base is not None and base == "*":
        return f"every {step} days of the week"
    names = compress_names(values, DAY_FULL)
    return f"on {names}"


def describe(parsed):
    expr = parsed["expr"]
    minute, hour = expr[0], expr[1]
    mvals, hvals = parsed["minute"], parsed["hour"]
    if minute != "*" and len(mvals) == 1 and hour != "*" and len(hvals) == 1:
        text = f"At {min(hvals):02d}:{min(mvals):02d}"
    elif minute == "*" and hour != "*" and len(hvals) == 1:
        text = f"Every minute during hour {min(hvals):02d}"
    else:
        mtext = minute_phrase(minute, mvals)
        htext = hour_phrase(hour, hvals)
        if htext == "of every hour" and minute != "*":
            htext = ""
        text = (mtext + " " + htext).strip()
        text = text[0].upper() + text[1:]

    dom = dom_phrase(expr[2], parsed["day of month"])
    dow = dow_phrase(expr[4], parsed["day of week"])
    if dom and dow:
        day = dom + " or " + dow
    else:
        day = dom or dow
    extras = []
    if day:
        extras.append(day)
    month = month_phrase(expr[3], parsed["month"])
    if month:
        extras.append(month)
    if extras:
        text += " " + ", ".join(extras)
    return text.rstrip(".") + "."


def matches(when, parsed):
    if when.minute not in parsed["minute"] or when.hour not in parsed["hour"]:
        return False
    if when.month not in parsed["month"]:
        return False
    cron_dow = (when.weekday() + 1) % 7
    dom_ok = when.day in parsed["day of month"]
    dow_ok = cron_dow in parsed["day of week"]
    if parsed["dom_star"] or parsed["dow_star"]:
        day_ok = dom_ok and dow_ok
    else:
        day_ok = dom_ok or dow_ok
    return day_ok


def next_runs(parsed, count, start=None):
    moment = (start or datetime.datetime.now()).replace(second=0, microsecond=0)
    moment += datetime.timedelta(minutes=1)
    limit = moment + datetime.timedelta(days=366 * 5)
    runs = []
    while len(runs) < count and moment <= limit:
        if matches(moment, parsed):
            runs.append(moment)
        moment += datetime.timedelta(minutes=1)
    return runs


def self_test():
    parsed = parse_cron("*/15 9-17 * * 1-5")
    assert parsed["minute"] == {0, 15, 30, 45}
    assert parsed["hour"] == set(range(9, 18))
    assert parsed["day of week"] == {1, 2, 3, 4, 5}
    assert parse_cron("0 0 * * 7")["day of week"] == {0}
    assert parse_cron("0 0 1 JAN MON")["month"] == {1}
    for bad in ("* * * *", "60 * * * *", "* 24 * * *", "* * 0 * *",
                "* * * 13 *", "* * * * 8", "*/0 * * * *", "* * 9-3 * *"):
        try:
            parse_cron(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted invalid expression {bad!r}")
    text = describe(parsed)
    assert text.startswith("Every 15 minutes") and "Monday through Friday" in text, text
    assert describe(parse_cron("30 2 * * *")) == "At 02:30."
    assert "every 2 hours" in describe(parse_cron("0 */2 * * *"))
    runs = next_runs(parse_cron("0 0 * * *"), 2, datetime.datetime(2024, 1, 1, 10, 0))
    assert runs == [datetime.datetime(2024, 1, 2), datetime.datetime(2024, 1, 3)], runs
    monday = next_runs(parse_cron("0 0 * * 1"), 1, datetime.datetime(2024, 1, 1, 0, 1))
    assert monday == [datetime.datetime(2024, 1, 8)], monday
    print("self-test OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("expression", nargs="?", help="quoted 5-field cron expression")
    ap.add_argument("--next", type=int, default=0, metavar="N",
                    help="also print the next N run times")
    ap.add_argument("--from", dest="start", metavar="TIME",
                    help="reference time for --next, 'YYYY-MM-DD HH:MM'")
    ap.add_argument("--self-test", action="store_true", help="run offline self tests")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.expression:
        ap.error("a cron expression is required")
    if args.next < 0:
        ap.error("--next must be >= 0")
    try:
        parsed = parse_cron(args.expression)
    except ValueError as exc:
        ap.error(f"invalid cron expression: {exc}")

    start = None
    if args.start:
        try:
            start = datetime.datetime.strptime(args.start, "%Y-%m-%d %H:%M")
        except ValueError:
            ap.error("--from must look like 'YYYY-MM-DD HH:MM'")

    print(describe(parsed))
    if args.next:
        runs = next_runs(parsed, args.next, start)
        for run in runs:
            print(run.strftime("%Y-%m-%d %H:%M"))
        if len(runs) < args.next:
            print(f"only {len(runs)} run(s) found within 5 years", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
