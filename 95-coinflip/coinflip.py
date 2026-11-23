#!/usr/bin/env python3
"""Flip coins, count results and show streaks."""
import argparse
import json
import random
import sys


def longest_streak(flips: list[str]) -> tuple[str | None, int]:
    best_side, best_len = None, 0
    run_side, run_len = None, 0
    for flip in flips:
        if flip == run_side:
            run_len += 1
        else:
            run_side, run_len = flip, 1
        if run_len > best_len:
            best_side, best_len = run_side, run_len
    return best_side, best_len


def flip(count: int, seed: int | None = None) -> dict:
    if not 1 <= count <= 1_000_000:
        raise ValueError("count must be between 1 and 1,000,000")
    rng = random.Random(seed) if seed is not None else random.SystemRandom()
    flips = [rng.choice("HT") for _ in range(count)]
    heads = flips.count("H")
    tails = count - heads
    side, length = longest_streak(flips)
    return {
        "count": count,
        "seed": seed,
        "flips": flips,
        "heads": heads,
        "tails": tails,
        "percentages": {"H": round(heads * 100 / count, 1), "T": round(tails * 100 / count, 1)},
        "longest_streak": {"side": side, "length": length},
    }


def self_test() -> None:
    assert longest_streak(list("HHHTT")) == ("H", 3)
    assert longest_streak(list("HTHTH")) == ("H", 1)
    assert longest_streak([]) == (None, 0)
    a, b = flip(200, seed=99), flip(200, seed=99)
    assert a == b, "seeded flips are not reproducible"
    assert a["heads"] + a["tails"] == 200
    assert len(a["flips"]) == 200
    assert a["percentages"]["H"] + a["percentages"]["T"] in (99.9, 100.0, 100.1)
    assert flip(1, seed=1)["longest_streak"]["length"] == 1
    try:
        flip(0)
    except ValueError:
        pass
    else:
        raise AssertionError("zero count accepted")
    print("self-test: ok (streaks, totals, seeded determinism)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Flip N coins and summarise the results.")
    ap.add_argument("-n", "--count", type=int, default=20, help="number of flips (default: 20)")
    ap.add_argument("--seed", type=int, help="seed for reproducible flips")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--self-test", action="store_true", help="run internal checks and exit")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    try:
        result = flip(args.count, args.seed)
    except ValueError as exc:
        print(f"coinflip: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    print("Flips: " + " ".join(result["flips"]))
    print(f"Heads: {result['heads']} ({result['percentages']['H']}%)")
    print(f"Tails: {result['tails']} ({result['percentages']['T']}%)")
    streak = result["longest_streak"]
    print(f"Longest streak: {streak['side']} x{streak['length']}")
    print("Distribution:")
    for side in ("H", "T"):
        count = result["heads"] if side == "H" else result["tails"]
        bar = "#" * round(count * 40 / result["count"])
        print(f"  {side} |{bar:<40}| {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
