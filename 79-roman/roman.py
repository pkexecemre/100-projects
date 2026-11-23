#!/usr/bin/env python3
"""Convert between integers (1-3999) and strict Roman numerals."""

import argparse
import json
import re
import sys

NUMERALS = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]
VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
PAIRS = {"IV": 4, "IX": 9, "XL": 40, "XC": 90, "CD": 400, "CM": 900}
ROMAN_RE = re.compile(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")


def to_roman(number):
    if isinstance(number, bool) or not isinstance(number, int):
        raise ValueError("value must be an integer")
    if not 1 <= number <= 3999:
        raise ValueError("value must be between 1 and 3999")
    parts = []
    remaining = number
    for value, symbol in NUMERALS:
        count, remaining = divmod(remaining, value)
        parts.append(symbol * count)
    return "".join(parts)


def from_roman(text):
    raw = text.strip().upper()
    if not raw:
        raise ValueError("empty Roman numeral")
    if not ROMAN_RE.fullmatch(raw):
        raise ValueError(f"not a well-formed Roman numeral: {text!r}")
    total = 0
    index = 0
    while index < len(raw):
        pair = raw[index:index + 2]
        if pair in PAIRS:
            total += PAIRS[pair]
            index += 2
        else:
            total += VALUES[raw[index]]
            index += 1
    if to_roman(total) != raw:
        raise ValueError(f"non-canonical Roman numeral: {text!r}")
    return total


def self_test():
    known = {
        1: "I", 4: "IV", 9: "IX", 14: "XIV", 40: "XL", 90: "XC",
        400: "CD", 900: "CM", 1994: "MCMXCIV", 2024: "MMXXIV",
        3999: "MMMCMXCIX",
    }
    for number, roman in known.items():
        assert to_roman(number) == roman, number
        assert from_roman(roman) == number, roman
        assert from_roman(roman.lower()) == number
    for bad_number in (0, -1, 4000, 10000):
        try:
            to_roman(bad_number)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted out-of-range {bad_number}")
    for bad_roman in ("", "IIII", "VV", "IC", "VX", "MMMM", "CMCM", "abc", "XIIX"):
        try:
            from_roman(bad_roman)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted invalid Roman numeral {bad_roman!r}")
    print("self-test: all checks passed")


def convert(text):
    raw = text.strip()
    if not raw:
        raise ValueError("empty value")
    if re.fullmatch(r"[+-]?\d+", raw):
        number = int(raw)
        return number, to_roman(number)
    number = from_roman(raw)
    return number, to_roman(number)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--self-test" in argv:
        self_test()
        return 0

    ap = argparse.ArgumentParser(
        description="Convert integers 1-3999 to Roman numerals and back.",
        epilog="Examples: roman.py 1994 | roman.py MCMXCIV | roman.py 42 --json",
    )
    ap.add_argument("value", help="integer 1-3999 or a Roman numeral")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    try:
        number, roman = convert(args.value)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"input": args.value, "value": number, "roman": roman},
                         indent=2))
    else:
        print(f"value {number}")
        print(f"roman {roman}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
