#!/usr/bin/env python3
"""Generate secure random passwords with class guarantees and entropy output."""

import argparse
import json
import math
import secrets
import string
import sys

SYMBOLS = "!@#$%^&*()-_=+[]{};:,.?/"
AMBIGUOUS = set("Il1O0o|`'\"")
MAX_COUNT = 10_000
MAX_LENGTH = 4096


def build_pools(use_upper=True, use_lower=True, use_digits=True,
                use_symbols=True, symbols=SYMBOLS, exclude_ambiguous=False):
    """Return one character pool per selected class, deduplicated and ordered."""
    pools = []
    for enabled, chars in ((use_lower, string.ascii_lowercase),
                           (use_upper, string.ascii_uppercase),
                           (use_digits, string.digits),
                           (use_symbols, symbols)):
        if not enabled:
            continue
        ordered = []
        for char in chars:
            if exclude_ambiguous and char in AMBIGUOUS:
                continue
            if char not in ordered:
                ordered.append(char)
        if ordered:
            pools.append(ordered)
    return pools


def entropy_bits(length, pools):
    size = len({char for pool in pools for char in pool})
    return length * math.log2(size) if size > 1 else 0.0


def generate_password(length, pools):
    """Pick at least one char from each class, fill, then Fisher-Yates shuffle."""
    if length < len(pools):
        raise ValueError("length must be at least the number of enabled classes (%d)"
                         % len(pools))
    chars = [secrets.choice(pool) for pool in pools]
    combined = [char for pool in pools for char in pool]
    chars.extend(secrets.choice(combined) for _ in range(length - len(chars)))
    for i in range(len(chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        chars[i], chars[j] = chars[j], chars[i]
    return "".join(chars)


def self_test():
    pools = build_pools()
    assert len(pools) == 4
    for _ in range(20):
        password = generate_password(12, pools)
        assert len(password) == 12
        assert any(c in string.ascii_lowercase for c in password)
        assert any(c in string.ascii_uppercase for c in password)
        assert any(c in string.digits for c in password)
        assert any(c in SYMBOLS for c in password)
    assert len({generate_password(16, pools) for _ in range(50)}) == 50

    small = build_pools(use_upper=False, use_digits=False, use_symbols=False)
    assert len(small) == 1
    assert entropy_bits(10, small) == 10 * math.log2(26)
    assert entropy_bits(16, pools) > 70

    clean = build_pools(exclude_ambiguous=True)
    all_chars = "".join("".join(pool) for pool in clean)
    assert not (set(all_chars) & AMBIGUOUS)
    try:
        generate_password(2, pools)
    except ValueError:
        pass
    else:
        raise AssertionError("short password should fail")
    print("self-test: 9 checks passed")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate secure passwords using the secrets module.")
    parser.add_argument("--length", type=int, default=16, metavar="N",
                        help="password length (default 16)")
    parser.add_argument("--count", type=int, default=1, metavar="N",
                        help="number of passwords (default 1)")
    parser.add_argument("--no-upper", action="store_true", help="exclude A-Z")
    parser.add_argument("--no-lower", action="store_true", help="exclude a-z")
    parser.add_argument("--no-digits", action="store_true", help="exclude 0-9")
    parser.add_argument("--no-symbols", action="store_true",
                        help="exclude punctuation")
    parser.add_argument("--symbols", default=SYMBOLS, metavar="CHARS",
                        help="custom symbol set")
    parser.add_argument("--exclude-ambiguous", action="store_true",
                        help="drop look-alike characters such as l, 1, O, 0")
    parser.add_argument("--entropy", action="store_true",
                        help="report entropy bits per password on stderr")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--self-test", action="store_true",
                        help="run offline checks and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        self_test()
        return 0
    if not 1 <= args.count <= MAX_COUNT:
        parser.error("--count must be between 1 and %d" % MAX_COUNT)
    if not 1 <= args.length <= MAX_LENGTH:
        parser.error("--length must be between 1 and %d" % MAX_LENGTH)

    pools = build_pools(not args.no_upper, not args.no_lower,
                        not args.no_digits, not args.no_symbols,
                        args.symbols, args.exclude_ambiguous)
    if not pools:
        print("passgen: error: no character classes enabled", file=sys.stderr)
        return 2
    if args.length < len(pools):
        print("passgen: error: length must be at least the number of enabled "
              "classes (%d)" % len(pools), file=sys.stderr)
        return 2

    passwords = [generate_password(args.length, pools) for _ in range(args.count)]
    bits = entropy_bits(args.length, pools)
    if args.json:
        print(json.dumps({
            "length": args.length,
            "count": args.count,
            "entropy_bits": round(bits, 2),
            "passwords": passwords,
        }, indent=2))
    else:
        for password in passwords:
            print(password)
        if args.entropy:
            print("entropy: %.2f bits per password (%d-character pool)" % (
                bits, len({char for pool in pools for char in pool})),
                file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
