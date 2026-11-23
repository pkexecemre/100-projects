#!/usr/bin/env python3
"""Timezone-aware timestamp toolbox: epoch, ISO 8601 and relative times."""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:  # pragma: no cover - Python < 3.9
    ZoneInfo = None


REL_RE = re.compile(
    r"^([+-]?\d+(?:\.\d+)?)\s*"
    r"(s|sec|secs|m|min|mins|h|hr|hrs|d|day|days|w|wk|wks|mo|y|yr|yrs)"
    r"(\s+ago)?$",
    re.IGNORECASE,
)
UNIT_SECONDS = {
    "s": 1, "sec": 1, "secs": 1, "m": 60, "min": 60, "mins": 60,
    "h": 3600, "hr": 3600, "hrs": 3600, "d": 86400, "day": 86400,
    "days": 86400, "w": 604800, "wk": 604800, "wks": 604800,
    "mo": 2592000, "y": 31536000, "yr": 31536000, "yrs": 31536000,
}


def parse_when(text, now=None):
    """Parse epoch seconds/ms, ISO 8601, 'now', or a signed relative span."""
    now = now or datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("reference time must be timezone-aware")
    raw = text.strip()
    if not raw:
        raise ValueError("empty timestamp")
    if raw.lower() == "now":
        return now.astimezone(timezone.utc)

    match = REL_RE.match(raw)
    if match:
        amount = float(match.group(1))
        seconds = amount * UNIT_SECONDS[match.group(2).lower()]
        if match.group(3):
            seconds = -seconds
        return (now + timedelta(seconds=seconds)).astimezone(timezone.utc)

    if re.fullmatch(r"[+-]?\d+(?:\.\d+)?", raw):
        value = float(raw)
        if abs(value) > 1e11:
            value /= 1000.0
        try:
            return datetime.fromtimestamp(value, timezone.utc)
        except (OverflowError, OSError, ValueError):
            raise ValueError(f"epoch out of range: {raw}")

    iso = raw
    if iso.endswith(("Z", "z")):
        iso = iso[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(iso)
    except ValueError:
        raise ValueError(
            f"cannot parse {raw!r}; use epoch, ISO 8601, or e.g. '-2h' / '30m ago'"
        )
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def human_delta(seconds):
    seconds = int(round(seconds))
    if abs(seconds) < 2:
        return "now"
    future = seconds > 0
    left = abs(seconds)
    chunks = []
    for size, label in ((86400 * 365, "y"), (86400 * 30, "mo"), (86400, "d"),
                        (3600, "h"), (60, "m"), (1, "s")):
        if left >= size and len(chunks) < 2:
            count, left = divmod(left, size)
            chunks.append(f"{count}{label}")
    text = " ".join(chunks) or "0s"
    return f"in {text}" if future else f"{text} ago"


def resolve_zone(name, utc):
    if utc:
        return timezone.utc
    if not name:
        return None  # system local rules, resolved per timestamp (DST-aware)
    if ZoneInfo is None:
        raise ValueError("timezone database unavailable; use --utc")
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError(f"unknown timezone: {name!r}")


def describe(text, zone, now=None):
    now = now or datetime.now(timezone.utc)
    when = parse_when(text, now)
    local = when.astimezone()
    selected = local if zone is None else when.astimezone(zone)
    payload = {
        "input": text,
        "epoch": int(when.timestamp()),
        "iso": selected.isoformat(),
        "utc": iso(when),
        "local": local.isoformat(),
        "timezone": selected.tzname() if zone is None else str(zone),
        "relative": human_delta((when - now).total_seconds()),
    }
    if when.microsecond:
        payload["epoch"] = when.timestamp()
    return payload


def self_test():
    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert parse_when("0", now) == datetime(1970, 1, 1, tzinfo=timezone.utc)
    assert parse_when("2024-01-01T03:00:00+03:00", now) == now
    assert parse_when("90m ago", now) == now - timedelta(minutes=90)
    assert parse_when("-2h", now) == now - timedelta(hours=2)
    assert parse_when("2024-06-01", now) == datetime(2024, 6, 1, tzinfo=timezone.utc)
    assert parse_when("1704067200000", now) == now  # milliseconds
    assert human_delta(5400) == "in 1h 30m"
    assert human_delta(-90) == "1m 30s ago"
    assert iso(now) == "2024-01-01T00:00:00Z"
    payload = describe("0", timezone.utc, now)
    assert payload["epoch"] == 0 and payload["utc"].startswith("1970-01-01")
    for bad in ("", "yesterday", "2024-13-01"):
        try:
            parse_when(bad, now)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted invalid timestamp {bad!r}")
    print("self-test: all checks passed")


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--self-test" in argv:
        self_test()
        return 0

    ap = argparse.ArgumentParser(
        description="Convert epoch, ISO 8601 and relative timestamps.",
        epilog="Examples: timestamp.py 1700000000 --utc | timestamp.py '-2h'",
    )
    ap.add_argument("when", nargs="?", default="now",
                    help="epoch seconds/ms, ISO 8601, now, or relative span")
    ap.add_argument("--utc", action="store_true", help="display in UTC")
    ap.add_argument("--tz", metavar="ZONE", help="IANA timezone, e.g. Europe/Berlin")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    # argparse mistakes "-2h" / "-3600" for an option; shield the leading dash
    # so negative timestamps still arrive as the positional value.
    shielded = ["\x00" + token if re.fullmatch(r"-\d.*", token) else token
                for token in argv]
    args = ap.parse_args(shielded)
    if args.when.startswith("\x00"):
        args.when = args.when[1:]
    if args.utc and args.tz:
        print("error: use either --utc or --tz, not both", file=sys.stderr)
        return 2
    try:
        zone = resolve_zone(args.tz, args.utc)
        payload = describe(args.when, zone)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for key in ("input", "epoch", "iso", "utc", "local", "timezone", "relative"):
            print(f"{key:<10} {payload[key]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
