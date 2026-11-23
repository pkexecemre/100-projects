#!/usr/bin/env python3
"""Dice notation roller with keep-high/low advantage and simulated stats."""

import argparse
import math
import random
import re
import sys
from collections import Counter

DICE_RE = re.compile(
    r"^(?:(\d+)\s*)?d\s*(\d+)\s*(?:(kh|kl)\s*(\d+))?\s*(?:([+-])\s*(\d+))?$"
)
ADV_WORDS = {"adv", "advantage"}
DIS_WORDS = {"dis", "disadvantage"}


def make_spec(count, sides, modifier=0, keep=None, keep_count=None):
    if not 1 <= count <= 100:
        raise ValueError("dice count must be between 1 and 100")
    if not 2 <= sides <= 1000:
        raise ValueError("sides must be between 2 and 1000")
    if not -10000 <= modifier <= 10000:
        raise ValueError("modifier must be between -10000 and 10000")
    if keep not in (None, "high", "low"):
        raise ValueError("keep must be high, low, or omitted")
    if keep is None:
        keep_count = count
    if keep_count is None or not 1 <= keep_count <= count:
        raise ValueError("kept dice must be between 1 and the dice count")
    return {
        "count": count,
        "sides": sides,
        "modifier": modifier,
        "keep": keep,
        "keep_count": keep_count,
    }


def parse(expr):
    """Parse notation like 2d6+3, d20, 4d6kh3, 2d20kl1, or 2d20 advantage."""
    if not isinstance(expr, str):
        raise ValueError("notation must be text")
    text = " ".join(expr.lower().split())
    if not text:
        raise ValueError("empty dice expression")
    if text in ADV_WORDS:
        return make_spec(2, 20, keep="high", keep_count=1)
    if text in DIS_WORDS:
        return make_spec(2, 20, keep="low", keep_count=1)

    mode = None
    words = text.split(" ")
    if words[-1] in ADV_WORDS:
        mode = "high"
        words.pop()
    elif words[-1] in DIS_WORDS:
        mode = "low"
        words.pop()
    text = " ".join(words)
    if not text:
        raise ValueError("missing dice before advantage/disadvantage")

    match = DICE_RE.match(text)
    if not match:
        raise ValueError(f"cannot parse dice notation: {expr!r}")
    count_text, sides_text, keep_text, kept_text, sign, mod_text = match.groups()
    count = int(count_text) if count_text else 1
    sides = int(sides_text)
    modifier = int((sign or "+") + (mod_text or "0"))
    keep = None
    keep_count = None
    if keep_text:
        if mode:
            raise ValueError("use either advantage/disadvantage or kh/kl, not both")
        keep = "high" if keep_text == "kh" else "low"
        keep_count = int(kept_text)

    if mode:
        count = max(count, 2)
        keep = mode
        keep_count = 1
    return make_spec(count, sides, modifier, keep, keep_count)


def describe(spec):
    text = f"{spec['count']}d{spec['sides']}"
    if spec["keep"]:
        tag = "kh" if spec["keep"] == "high" else "kl"
        text += f"{tag}{spec['keep_count']}"
    if spec["modifier"]:
        text += f"{spec['modifier']:+d}"
    return text


def roll(spec, rng):
    """Roll the dice once and return rolls, kept dice, dropped dice, and total."""
    rolls = [rng.randint(1, spec["sides"]) for _ in range(spec["count"])]
    if spec["keep"]:
        reverse = spec["keep"] == "high"
        order = sorted(range(len(rolls)), key=lambda i: rolls[i], reverse=reverse)
        chosen = order[: spec["keep_count"]]
        kept = [rolls[i] for i in chosen]
        dropped = [rolls[i] for i in range(len(rolls)) if i not in set(chosen)]
    else:
        kept = list(rolls)
        dropped = []
    total = sum(kept) + spec["modifier"]
    return {
        "spec": spec,
        "rolls": rolls,
        "kept": kept,
        "dropped": dropped,
        "total": total,
    }


def format_result(result):
    spec = result["spec"]
    text = f"{describe(spec)} -> {result['rolls']}"
    if spec["keep"]:
        text += f" keep {result['kept']} (drop {result['dropped']})"
    if spec["modifier"]:
        text += f" {spec['modifier']:+d}"
    return text + f" = {result['total']}"


def roll_stats(spec, trials, rng):
    totals = [roll(spec, rng)["total"] for _ in range(trials)]
    mean = sum(totals) / trials
    variance = sum((value - mean) ** 2 for value in totals) / trials
    return {
        "trials": trials,
        "min": min(totals),
        "max": max(totals),
        "mean": mean,
        "stdev": math.sqrt(variance),
        "counts": Counter(totals),
    }


def stats_report(spec, stats):
    lines = [
        f"{describe(spec)} over {stats['trials']} rolls",
        f"min {stats['min']}  max {stats['max']}  "
        f"mean {stats['mean']:.3f}  stdev {stats['stdev']:.3f}",
    ]
    counts = stats["counts"]
    peak = max(counts.values())
    values = sorted(counts)
    if len(values) > 40:
        lines.append("(histogram limited to the 40 most common totals)")
        values = sorted(counts, key=lambda value: (-counts[value], value))[:40]
        values.sort()
    for value in values:
        bar = "#" * max(1, round(counts[value] * 40 / peak))
        lines.append(f"{value:>6} {counts[value]:>7} {bar}")
    return "\n".join(lines)


def play(seed):
    rng = random.Random(seed)
    print("Dice roller. Try 2d6+3, d20, 4d6kh3, 2d20 advantage, or q to quit.")
    while True:
        try:
            text = input("dice> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if text.lower() in ("q", "quit"):
            return 0
        if not text:
            continue
        try:
            spec = parse(text)
        except ValueError as exc:
            print(f"error: {exc}")
            continue
        print(format_result(roll(spec, rng)))


def self_test():
    checks = 0

    spec = parse("2d6+3")
    assert (spec["count"], spec["sides"], spec["modifier"]) == (2, 6, 3)
    assert spec["keep"] is None and spec["keep_count"] == 2
    spec = parse("d20")
    assert (spec["count"], spec["sides"], spec["modifier"]) == (1, 20, 0)
    spec = parse("4d6kh3-1")
    assert spec["keep"] == "high" and spec["keep_count"] == 3 and spec["modifier"] == -1
    spec = parse("2d20kl1")
    assert spec["keep"] == "low" and spec["keep_count"] == 1
    checks += 1

    for text in ("2d20 advantage", "2d20 adv", "d20 adv", "adv", "advantage"):
        spec = parse(text)
        assert spec["count"] >= 2 and spec["sides"] == 20
        assert spec["keep"] == "high" and spec["keep_count"] == 1, text
    for text in ("2d20 disadvantage", "dis", "d20 dis"):
        spec = parse(text)
        assert spec["keep"] == "low" and spec["keep_count"] == 1, text
    checks += 1

    for bad in [
        "", "d", "2d", "0d6", "101d6", "1d1", "1d1001", "2d6kh5", "2d6kh0",
        "2d6+", "2d6x", "1d6+10001", "2d6 advantage kh1", "fireball",
    ]:
        try:
            parse(bad)
            raise AssertionError(f"expected ValueError for {bad!r}")
        except ValueError:
            pass
    checks += 1

    class ScriptedRng:
        def __init__(self, values):
            self.values = list(values)
            self.index = 0

        def randint(self, low, high):
            assert low == 1
            value = self.values[self.index]
            self.index += 1
            assert 1 <= value <= high
            return value

    result = roll(parse("2d6+3"), ScriptedRng([2, 5]))
    assert result["rolls"] == [2, 5] and result["total"] == 10
    assert result["dropped"] == []
    result = roll(parse("4d6kh3"), ScriptedRng([1, 6, 3, 4]))
    assert result["kept"] == [6, 4, 3] and result["dropped"] == [1] and result["total"] == 13
    result = roll(parse("2d20kl1"), ScriptedRng([20, 4]))
    assert result["kept"] == [4] and result["total"] == 4
    result = roll(parse("2d20 advantage"), ScriptedRng([20, 1]))
    assert result["total"] == 20
    checks += 1

    for text in ("2d6+3", "4d6kh3", "2d20kl1", "d20", "1d8-2"):
        spec = parse(text)
        again = parse(describe(spec))
        assert again == spec, (text, describe(spec), again)
    checks += 1

    rng = random.Random(7)
    spec = parse("2d6+3")
    stats = roll_stats(spec, 2000, rng)
    assert stats["trials"] == 2000
    assert sum(stats["counts"].values()) == 2000
    assert stats["min"] >= 5 and stats["max"] <= 15
    assert 9.5 < stats["mean"] < 10.5
    assert 1.5 < stats["stdev"] < 3.5
    report = stats_report(spec, stats)
    assert "mean" in report and "#" in report
    checks += 1

    assert describe(parse("2d20 adv")) == "2d20kh1"
    assert "keep [6, 4, 3]" in format_result(roll(parse("4d6kh3"), ScriptedRng([1, 6, 3, 4])))
    checks += 1

    print(f"40-dice: self-test passed ({checks} groups)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Roll dice from notation, with keep-high/low and simulated statistics.",
    )
    ap.add_argument("notation", nargs="?", help="e.g. 2d6+3, d20, 4d6kh3, 2d20 advantage")
    ap.add_argument("--times", type=int, default=1, help="roll the notation N times (default 1)")
    ap.add_argument("--stats", type=int, metavar="N", help="simulate N rolls and print statistics")
    ap.add_argument("--seed", type=int, default=None, help="seed the random generator")
    ap.add_argument("--self-test", action="store_true", help="run parser/roller tests and exit")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.times < 1 or args.times > 1000:
        ap.error("--times must be between 1 and 1000")
    if args.stats is not None:
        if args.stats < 1:
            ap.error("--stats must be at least 1")
        if not args.notation:
            ap.error("--stats requires a dice notation")
        if args.times != 1:
            ap.error("--stats cannot be combined with --times")
    elif args.times != 1 and not args.notation:
        ap.error("--times requires a dice notation")

    if not args.notation:
        return play(args.seed)

    try:
        spec = parse(args.notation)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    rng = random.Random(args.seed)
    if args.stats is not None:
        print(stats_report(spec, roll_stats(spec, args.stats, rng)))
        return 0

    results = [roll(spec, rng) for _ in range(args.times)]
    if args.times == 1:
        print(format_result(results[0]))
        return 0
    for index, result in enumerate(results, 1):
        print(f"{index:>3}: {result['total']:>5}   {result['rolls']}")
    totals = [result["total"] for result in results]
    print(
        f"\n{args.times} rolls of {describe(spec)}: "
        f"total {sum(totals)}  mean {sum(totals) / len(totals):.2f}  "
        f"min {min(totals)}  max {max(totals)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
