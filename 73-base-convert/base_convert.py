#!/usr/bin/env python3
"""Convert integers between binary, octal, decimal and hexadecimal."""

import argparse
import json
import re
import sys

PREFIXES = {"0b": (2, "bin"), "0o": (8, "oct"), "0x": (16, "hex")}
FORMATS = {
    "bin": (2, "0b"),
    "oct": (8, "0o"),
    "dec": (10, ""),
    "hex": (16, "0x"),
}


def parse_int(text):
    """Parse 0b/0o/0x-prefixed or plain decimal text. Returns an int."""
    raw = text.strip().replace("_", "")
    if not raw:
        raise ValueError("empty value")
    sign = 1
    if raw[0] in "+-":
        if raw[0] == "-":
            sign = -1
        raw = raw[1:]
    if not raw:
        raise ValueError("missing digits after sign")

    base, name = 10, "dec"
    for prefix, spec in PREFIXES.items():
        if raw[:2].lower() == prefix:
            base, name = spec
            raw = raw[2:]
            break
    if not raw:
        raise ValueError("missing digits after prefix")

    valid = {
        2: set("01"),
        8: set("01234567"),
        10: set("0123456789"),
        16: set("0123456789abcdefABCDEF"),
    }[base]
    bad = next((ch for ch in raw if ch not in valid), None)
    if bad is not None:
        raise ValueError(f"invalid digit {bad!r} for base {base} ({name})")
    return sign * int(raw, base)


def render(value, target):
    base, prefix = FORMATS[target]
    sign = "-" if value < 0 else ""
    if base == 10:
        return f"{value}"
    digits = format(abs(value), {2: "b", 8: "o", 16: "x"}[base])
    return f"{sign}{prefix}{digits}"


def self_test():
    cases = {
        "0xff": 255, "0XFF": 255, "-0x10": -16, "0b1010": 10, "0o17": 15,
        "42": 42, "+7": 7, "0": 0, "1_000": 1000,
    }
    for text, expected in cases.items():
        assert parse_int(text) == expected, (text, parse_int(text))
    assert render(255, "hex") == "0xff"
    assert render(10, "bin") == "0b1010"
    assert render(-8, "oct") == "-0o10"
    assert render(0, "hex") == "0x0"
    for bad in ("", "0x", "0b102", "0o8", "12z", "-", "+0x"):
        try:
            parse_int(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted invalid input {bad!r}")
    assert parse_int(render(-255, "hex")) == -255
    print("self-test: all checks passed")


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--self-test" in argv:
        self_test()
        return 0

    ap = argparse.ArgumentParser(
        description="Convert an integer across bin/oct/dec/hex.",
        epilog="Examples: base_convert.py 0xff | base_convert.py 42 --to bin",
    )
    ap.add_argument("value", help="integer with optional 0b/0o/0x prefix")
    ap.add_argument("--to", choices=sorted(FORMATS), help="print a single base")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    # Shield negative values ("-0x10", "-42") from argparse's option parser.
    shielded = ["\x00" + token if re.fullmatch(r"-\d.*", token) else token
                for token in argv]
    args = ap.parse_args(shielded)
    if args.value.startswith("\x00"):
        args.value = args.value[1:]

    try:
        value = parse_int(args.value)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.to:
        print(render(value, args.to))
        return 0

    payload = {
        "input": args.value,
        "decimal": value,
        "bin": render(value, "bin"),
        "oct": render(value, "oct"),
        "hex": render(value, "hex"),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"dec  {payload['decimal']}")
        print(f"bin  {payload['bin']}")
        print(f"oct  {payload['oct']}")
        print(f"hex  {payload['hex']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
