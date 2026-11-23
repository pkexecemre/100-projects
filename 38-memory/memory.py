#!/usr/bin/env python3
"""Memory matching pairs on a text grid, with seedable shuffles and self-test."""

import argparse
import random
import sys


def make_deck(pairs):
    """Build a row-major deck of letter labels, two cards per label."""
    if pairs < 1 or pairs > 26:
        raise ValueError("pairs must be between 1 and 26")
    labels = [chr(ord("A") + index) for index in range(pairs)]
    return [label for label in labels for _ in range(2)]


def shuffled(deck, seed=None):
    cards = list(deck)
    random.Random(seed).shuffle(cards)
    return cards


def is_match(deck, first, second):
    return first != second and deck[first] == deck[second]


def all_matched(deck, matched):
    return len(matched) == len(deck)


def render(deck, cols, matched, visible=()):
    rows = len(deck) // cols
    lines = ["    " + "".join(f"{c + 1:>4}" for c in range(cols))]
    for row in range(rows):
        cells = []
        for col in range(cols):
            index = row * cols + col
            if index in matched or index in visible:
                cells.append(f" {deck[index]}  ")
            else:
                cells.append(f"[{index + 1:>2}]")
        lines.append(f"{row + 1:>2}  " + "".join(cells))
    return "\n".join(lines)


def play(rows, cols, seed):
    total = rows * cols
    pairs = total // 2
    deck = shuffled(make_deck(pairs), seed)
    matched = set()
    turns = 0

    print(f"Memory {rows}x{cols}: {pairs} pairs. Match two cards per turn.")
    print("Enter card numbers, or q to quit.\n")

    while not all_matched(deck, matched):
        print(render(deck, cols, matched))
        print()
        picks = []
        while len(picks) < 2:
            try:
                text = input(f"card {len(picks) + 1} (1-{total}, q)> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            if text.lower() in ("q", "quit"):
                return 0
            try:
                choice = int(text) - 1
            except ValueError:
                print(f"error: enter a card number from 1 to {total}.\n")
                continue
            if not 0 <= choice < total:
                print(f"error: card must be between 1 and {total}.\n")
                continue
            if choice in matched:
                print("error: that card is already matched.\n")
                continue
            if choice in picks:
                print("error: pick a different second card.\n")
                continue
            picks.append(choice)
            print(render(deck, cols, matched, visible=picks))
            print()

        turns += 1
        if is_match(deck, *picks):
            matched.update(picks)
            print(f"Match: {deck[picks[0]]}!\n")
        else:
            print(f"No match: {deck[picks[0]]} and {deck[picks[1]]}.\n")

    print(render(deck, cols, matched))
    print(f"\nSolved in {turns} turns ({pairs} pairs). Perfect is {pairs}.")
    return 0


def self_test():
    checks = 0

    deck = make_deck(4)
    assert deck == ["A", "A", "B", "B", "C", "C", "D", "D"]
    assert len(make_deck(26)) == 52
    for bad in (0, 27):
        try:
            make_deck(bad)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass
    checks += 1

    deck = make_deck(8)
    shuffled_deck = shuffled(deck, seed=5)
    assert sorted(shuffled_deck) == sorted(deck)
    assert len(shuffled_deck) == len(deck)
    assert shuffled_deck == shuffled(deck, seed=5)
    assert any(shuffled(deck, seed=s) != deck for s in range(10))
    checks += 1

    deck = ["A", "B", "A", "B"]
    assert is_match(deck, 0, 2)
    assert is_match(deck, 1, 3)
    assert not is_match(deck, 0, 1)
    assert not is_match(deck, 0, 0)
    assert not is_match(deck, 2, 3)
    checks += 1

    deck = make_deck(3)
    matched = {0, 1}
    assert not all_matched(deck, matched)
    matched = set(range(6))
    assert all_matched(deck, matched)
    checks += 1

    deck = shuffled(make_deck(8), seed=2)
    art = render(deck, 4, set())
    assert "[ 1]" in art and "[16]" in art
    assert render(deck, 4, {0}).count(deck[0]) == 1
    assert render(deck, 4, set(), visible=(0,)).count(deck[0]) == 1
    checks += 1

    deck = shuffled(make_deck(8), seed=11)
    positions = {}
    for index, label in enumerate(deck):
        positions.setdefault(label, []).append(index)
    matched = set()
    turns = 0
    for label in sorted(positions):
        first, second = positions[label]
        assert is_match(deck, first, second)
        matched.update((first, second))
        turns += 1
    assert len(matched) == 16
    assert all_matched(deck, matched)
    assert turns == 8
    checks += 1

    print(f"38-memory: self-test passed ({checks} groups)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Memory matching pairs on a text grid.")
    ap.add_argument("--rows", type=int, default=4, help="grid rows (default 4)")
    ap.add_argument("--cols", type=int, default=4, help="grid columns (default 4)")
    ap.add_argument("--seed", type=int, default=None, help="seed the shuffle")
    ap.add_argument("--self-test", action="store_true", help="run deck/match tests and exit")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not 2 <= args.rows <= 6:
        ap.error("--rows must be between 2 and 6")
    if not 2 <= args.cols <= 9:
        ap.error("--cols must be between 2 and 9")
    if (args.rows * args.cols) % 2:
        ap.error("rows times cols must be even")
    if args.rows * args.cols > 52:
        ap.error("the grid may hold at most 52 cards")
    return play(args.rows, args.cols, args.seed)


if __name__ == "__main__":
    sys.exit(main())
