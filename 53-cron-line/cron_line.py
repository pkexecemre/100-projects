#!/usr/bin/env python3
"""Validate a cron schedule and command, then print a ready-to-paste crontab line."""
import argparse
import os
import sys
from datetime import datetime, timedelta

MACROS = {
    "@reboot": None,
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}
NAMES = ["minute", "hour", "day of month", "month", "day of week"]
LIMITS = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]
MONTH_NAMES = {name: i + 1 for i, name in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}
DOW_NAMES = {name: i for i, name in enumerate("sun mon tue wed thu fri sat".split())}


def value_of(token, index):
    text = token.strip().lower()
    table = MONTH_NAMES if index == 3 else DOW_NAMES if index == 4 else {}
    if text in table:
        return table[text]
    if not text.isdigit():
        raise ValueError(f"{NAMES[index]}: {token!r} is not a number or known name")
    value = int(text)
    low, high = LIMITS[index]
    if value < low or value > high:
        raise ValueError(f"{NAMES[index]}: {value} is outside {low}-{high}")
    return value


def parse_field(text, index):
    if not text:
        raise ValueError(f"{NAMES[index]}: field is empty")
    values = set()
    for part in text.split(","):
        if not part:
            raise ValueError(f"{NAMES[index]}: empty list item")
        body, slash, step_text = part.partition("/")
        step = 1
        if slash:
            if not step_text.isdigit() or int(step_text) < 1:
                raise ValueError(f"{NAMES[index]}: invalid step in {part!r}")
            step = int(step_text)
        if body == "*":
            start, end = LIMITS[index]
        elif "-" in body:
            left, _, right = body.partition("-")
            start, end = value_of(left, index), value_of(right, index)
            if start > end:
                raise ValueError(f"{NAMES[index]}: reversed range in {part!r}")
        else:
            start = value_of(body, index)
            end = LIMITS[index][1] if slash else start
        values.update(range(start, end + 1, step))
    if index == 4 and 7 in values:
        values.discard(7)
        values.add(0)
    if not values:
        raise ValueError(f"{NAMES[index]}: no values in {text!r}")
    return values


def parse_schedule(text):
    raw = text.strip()
    if not raw:
        raise ValueError("schedule is empty")
    if raw in MACROS:
        expanded = MACROS[raw]
        if expanded is None:
            return {"fields": None, "text": raw}
        raw = expanded
    parts = raw.split()
    if len(parts) != 5:
        raise ValueError(f"schedule needs 5 fields or a macro, got {len(parts)} in {text!r}")
    fields = tuple(parse_field(part, index) for index, part in enumerate(parts))
    return {"fields": fields, "text": " ".join(parts)}


def matches(moment, schedule):
    fields = schedule["fields"]
    if fields is None:
        return False
    minute, hour, dom, month, dow = fields
    if moment.minute not in minute or moment.hour not in hour or moment.month not in month:
        return False
    parts = schedule["text"].split()
    dom_star = parts[2] == "*"
    dow_star = parts[4] == "*"
    day_ok = moment.day in dom
    week_ok = (moment.weekday() + 1) % 7 in dow
    if dom_star or dow_star:
        return day_ok and week_ok
    return day_ok or week_ok


def next_runs(schedule, start=None, count=3):
    if schedule["fields"] is None:
        return []
    current = (start or datetime.now()).replace(second=0, microsecond=0) + timedelta(minutes=1)
    limit = current + timedelta(days=366 * 5)
    found = []
    while current < limit and len(found) < count:
        if matches(current, schedule):
            found.append(current)
        current += timedelta(minutes=1)
    return found


def summary(schedule):
    if schedule["fields"] is None:
        return "runs once at system boot"
    minute, hour, dom, month, dow = schedule["text"].split()
    if minute == "*" and hour == "*":
        text = "runs every minute"
    elif minute.startswith("*/") and minute[2:].isdigit() and hour == "*":
        text = f"runs every {minute[2:]} minutes"
    elif minute.isdigit() and hour == "*":
        text = f"runs at minute {minute} of every hour"
    elif minute.isdigit() and hour.isdigit():
        clock = f"{int(hour):02d}:{int(minute):02d}"
        text = f"runs daily at {clock}" if month == "*" and dom == "*" and dow == "*" else f"runs at {clock}"
    else:
        text = f"runs at minute {minute} past hour {hour}"
    if month != "*":
        text += f" in month(s) {month}"
    if dom != "*":
        text += f" on day(s) {dom}"
    if dow != "*":
        text += f" on weekday(s) {dow}"
    return text


def validate_command(command):
    command = command.strip()
    if not command:
        raise ValueError("command is empty")
    if "\n" in command or "\r" in command:
        raise ValueError("command must be a single line")
    for index, char in enumerate(command):
        if char == "%" and (index == 0 or command[index - 1] != "\\"):
            raise ValueError("unescaped % in command: cron turns it into a newline; write \\% for a literal percent")
    return command


def command_note(command):
    first = command.split()[0]
    if os.path.isabs(first) or first.startswith("$") or first.startswith("./"):
        return None
    return "cron uses a minimal PATH; an absolute program path is safer"


def build_line(schedule, command, name=None):
    comment = [f"# job: {name}"] if name else []
    comment.append(f"# {summary(schedule)}")
    upcoming = next_runs(schedule)
    if upcoming:
        comment.append("# next: " + ", ".join(moment.strftime("%Y-%m-%d %H:%M") for moment in upcoming))
    note = command_note(command)
    if note:
        comment.append(f"# note: {note}")
    return "\n".join(comment + [f"{schedule['text']} {command}"])


def self_test():
    fields = parse_schedule("*/15 9-17 * * mon-fri")["fields"]
    assert fields[0] == {0, 15, 30, 45} and fields[1] == set(range(9, 18))
    assert fields[4] == {1, 2, 3, 4, 5}
    assert parse_schedule("@daily")["text"] == "0 0 * * *"
    assert parse_schedule("@reboot")["fields"] is None
    for bad in ("61 * * * *", "* * * *", "*/0 * * * *", "0 0 0 * *"):
        try:
            parse_schedule(bad)
            raise AssertionError(f"accepted bad schedule: {bad}")
        except ValueError:
            pass
    runs = next_runs(parse_schedule("0 0 * * *"), datetime(2026, 1, 1, 12, 0), 2)
    assert [moment.isoformat() for moment in runs] == ["2026-01-02T00:00:00", "2026-01-03T00:00:00"]
    assert parse_schedule("30 4 * * sun")["fields"][4] == {0}
    assert summary(parse_schedule("0 0 * * *")) == "runs daily at 00:00"
    assert summary(parse_schedule("0 0 * * mon")) == "runs at 00:00 on weekday(s) mon"
    assert summary(parse_schedule("0 0 1 * *")) == "runs at 00:00 on day(s) 1"
    for bad in ("echo hi\nrm -rf /", "date +%s", ""):
        try:
            validate_command(bad)
            raise AssertionError(f"accepted bad command: {bad!r}")
        except ValueError:
            pass
    assert validate_command(r"date +\%s") == r"date +\%s"
    line = build_line(parse_schedule("*/5 * * * *"), "/usr/bin/logger hi", "ping")
    assert line.splitlines()[-1] == "*/5 * * * * /usr/bin/logger hi"
    assert "# job: ping" in line and "# next:" in line
    print("self-test: ok")
    return 0


def main():
    if "--self-test" in sys.argv[1:]:
        return self_test()
    parser = argparse.ArgumentParser(description="Validate a cron schedule and command, then emit the crontab line.")
    parser.add_argument("schedule", help='five fields or a macro like "@daily"')
    parser.add_argument("--name", help="label shown in the comment header, before the schedule")
    args, extra = parser.parse_known_args()
    words = [word for word in extra if word != "--"]
    command = " ".join(words)
    try:
        schedule = parse_schedule(args.schedule)
        command = validate_command(command)
        print(build_line(schedule, command, args.name))
    except ValueError as exc:
        print(f"cron-line: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
