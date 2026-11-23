#!/usr/bin/env python3
"""Generate UUID version 4 values in bulk."""

import argparse
import re
import sys
import uuid

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
MAX_COUNT = 1_000_000


def generate(count=1, prefix="", suffix="", upper=False, dashes=True):
    for _ in range(count):
        value = str(uuid.uuid4())
        if not dashes:
            value = value.replace("-", "")
        if upper:
            value = value.upper()
        yield prefix + value + suffix


def self_test():
    values = list(generate(100))
    assert len(values) == 100
    assert len(set(values)) == 100
    assert all(UUID_RE.match(value) for value in values)
    assert values[0][14] == "4"
    assert values[0][19] in "89ab"

    custom = list(generate(2, prefix="id_", suffix=".txt", upper=True, dashes=False))
    assert all(value.startswith("id_") and value.endswith(".txt") for value in custom)
    assert all(value[3:35].isupper() for value in custom)
    assert all("-" not in value for value in custom)
    assert len(list(generate(0))) == 0
    print("self-test: 8 checks passed")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate random UUID version 4 values.")
    parser.add_argument("--count", type=int, default=1, metavar="N",
                        help="number of UUIDs to generate (default 1)")
    parser.add_argument("--prefix", default="", help="text before each UUID")
    parser.add_argument("--suffix", default="", help="text after each UUID")
    parser.add_argument("--upper", action="store_true", help="uppercase output")
    parser.add_argument("--no-dashes", action="store_true",
                        help="omit the hyphens")
    parser.add_argument("--self-test", action="store_true",
                        help="run offline checks and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        self_test()
        return 0
    if not 1 <= args.count <= MAX_COUNT:
        parser.error("--count must be between 1 and %d" % MAX_COUNT)

    for value in generate(args.count, args.prefix, args.suffix,
                          args.upper, not args.no_dashes):
        print(value)
    return 0


if __name__ == "__main__":
    sys.exit(main())
