#!/usr/bin/env python3
"""Convert between byte, duration, length and weight units.

Byte units use decimal (SI) and binary (IEC) prefixes.  All conversion
factors are exact definitions: 1 in = 0.0254 m, 1 lb = 0.45359237 kg, etc.
"""

import argparse
import json
import math
import sys

REGISTRY = {
    "bytes": {
        "base": "B",
        "units": {
            "B": 1,
            "KB": 1000, "MB": 1000 ** 2, "GB": 1000 ** 3,
            "TB": 1000 ** 4, "PB": 1000 ** 5,
            "KiB": 1024, "MiB": 1024 ** 2, "GiB": 1024 ** 3,
            "TiB": 1024 ** 4, "PiB": 1024 ** 5,
        },
    },
    "duration": {
        "base": "s",
        "units": {
            "ns": 1e-9, "us": 1e-6, "ms": 1e-3, "s": 1, "min": 60,
            "h": 3600, "d": 86400, "wk": 604800,
        },
    },
    "length": {
        "base": "m",
        "units": {
            "mm": 0.001, "cm": 0.01, "m": 1, "km": 1000,
            "in": 0.0254, "ft": 0.3048, "yd": 0.9144, "mi": 1609.344,
        },
    },
    "weight": {
        "base": "kg",
        "units": {
            "mg": 1e-6, "g": 0.001, "kg": 1, "t": 1000,
            "oz": 0.028349523125, "lb": 0.45359237,
        },
    },
}

LOOKUP = {}
for _category, _spec in REGISTRY.items():
    for _unit in _spec["units"]:
        LOOKUP.setdefault(_unit.lower(), []).append((_category, _unit))


def resolve(name):
    """Return (category, canonical unit) for a unit name."""
    hits = LOOKUP.get(name.strip().lower(), [])
    if not hits:
        raise ValueError(f"unknown unit: {name!r}")
    if len(hits) > 1:
        cats = ", ".join(c for c, _ in hits)
        raise ValueError(f"ambiguous unit {name!r} (in {cats})")
    return hits[0]


def convert(value, from_unit, to_unit):
    cat_a, ua = resolve(from_unit)
    cat_b, ub = resolve(to_unit)
    if cat_a != cat_b:
        raise ValueError(f"cannot convert {ua} ({cat_a}) to {ub} ({cat_b})")
    factor_a = REGISTRY[cat_a]["units"][ua]
    factor_b = REGISTRY[cat_b]["units"][ub]
    return cat_a, value * factor_a / factor_b


def number(value, precision=12):
    """Compact representation: int when integral, else significant digits."""
    if not math.isfinite(value):
        raise ValueError("result is not finite")
    if value == 0:
        return "0"
    if value.is_integer() and abs(value) < 1e18:
        return str(int(value))
    return f"{value:.{precision}g}"


def list_units():
    for category, spec in REGISTRY.items():
        print(f"{category} (base: {spec['base']})")
        for unit, factor in spec["units"].items():
            print(f"  {unit:<5} {factor:g} {spec['base']}")
        print()


def self_test():
    cases = [
        (1, "GiB", "B", 1073741824),
        (1, "GB", "MiB", 1000000000 / 1048576),
        (1, "h", "min", 60),
        (1, "mi", "m", 1609.344),
        (1, "lb", "kg", 0.45359237),
        (100, "cm", "in", 100 / 2.54),
    ]
    for value, src, dst, expected in cases:
        _, got = convert(value, src, dst)
        assert math.isclose(got, expected, rel_tol=1e-12), (src, dst, got)
    _, back = convert(1073741824, "B", "GiB")
    assert math.isclose(back, 1.0, rel_tol=1e-12)
    assert resolve("kib") == ("bytes", "KiB")
    assert resolve("MIN") == ("duration", "min")
    try:
        convert(1, "GB", "m")
    except ValueError:
        pass
    else:
        raise AssertionError("cross-category conversion was accepted")
    print("self-test: all checks passed")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Convert bytes, durations, lengths and weights.",
        epilog="Example: unit_convert.py 1.5 GiB MB",
    )
    ap.add_argument("value", nargs="?", help="numeric amount")
    ap.add_argument("from_unit", nargs="?", help="source unit (e.g. GiB, h, mi)")
    ap.add_argument("to_unit", nargs="?", help="target unit (e.g. MB, min, km)")
    ap.add_argument("--list", action="store_true", help="show the unit registry")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--precision", type=int, default=12,
                    help="significant digits (default 12)")
    ap.add_argument("--self-test", action="store_true", help="run built-in checks")
    args = ap.parse_args(argv)

    if args.self_test:
        self_test()
        return 0
    if args.list:
        list_units()
        return 0
    if args.value is None or args.from_unit is None or args.to_unit is None:
        ap.print_usage(sys.stderr)
        print("error: VALUE FROM_UNIT TO_UNIT are required", file=sys.stderr)
        return 2
    if args.precision < 1 or args.precision > 17:
        print("error: --precision must be between 1 and 17", file=sys.stderr)
        return 2
    try:
        value = float(args.value.replace("_", ""))
        if not math.isfinite(value):
            raise ValueError("amount must be finite")
        category, result = convert(value, args.from_unit, args.to_unit)
        text = number(result, args.precision)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    _, src = resolve(args.from_unit)
    _, dst = resolve(args.to_unit)
    if args.json:
        payload = {
            "value": value,
            "from": src,
            "to": dst,
            "category": category,
            "result": float(text),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"{number(value)} {src} = {text} {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
