#!/usr/bin/env python3
"""Number guessing with higher/lower hints, plus a binary-search computer mode."""

import argparse
import math
import random
import sys


def optimal_bound(high):
    """Worst-case guesses for binary search over 1..high."""
    return max(1, math.ceil(math.log2(high + 1)))


def hint(secret, guess):
    if guess < secret:
        return "higher"
    if guess > secret:
        return "lower"
    return "correct"


def parse_guess(text, low, high):
    try:
        value = int(text)
    except ValueError:
        raise ValueError("guess must be a whole number") from None
    if not low <= value <= high:
        raise ValueError(f"guess must be between {low} and {high}")
    return value


def binary_guess(low, high):
    return (low + high) // 2


def apply_response(low, high, guess, response):
    """Narrow the feasible range after a hint. Returns the new (low, high)."""
    if response == "higher":
        return guess + 1, high
    if response == "lower":
        return low, guess - 1
    if response == "correct":
        return guess, guess
    raise ValueError(f"unknown response: {response}")


def guesses_label(count):
    return f"{count} guess" if count == 1 else f"{count} guesses"


def player_game(high, seed):
    rng = random.Random(seed)
    secret = rng.randint(1, high)
    low, high_now = 1, high
    attempts = 0

    print(f"I picked a number from 1 to {high}.")
    print(f"Binary search needs at most {optimal_bound(high)} guesses. Good luck.\n")

    while True:
        try:
            text = input(f"guess ({low}-{high_now}, q)> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if text.lower() in ("q", "quit"):
            return 0
        try:
            guess = parse_guess(text, low, high_now)
        except ValueError as exc:
            print(f"error: {exc}.\n")
            continue

        attempts += 1
        result = hint(secret, guess)
        if result == "correct":
            print(f"\nCorrect! {secret} in {guesses_label(attempts)}.")
            print(f"Optimal worst case from this range: {optimal_bound(high)}.")
            return 0
        print(f"{guess} is too {'low' if result == 'higher' else 'high'} - go {result}.")
        low, high_now = apply_response(low, high_now, guess, result)
        print(f"Range is now {low}-{high_now}.\n")


def computer_game(high):
    low, high_now = 1, high
    guesses = 0
    print(f"Think of a number from 1 to {high}. I will binary-search it.")
    print("Answer with c (correct), h (higher), or l (lower).\n")
    try:
        input("Press Enter when ready...")
    except (EOFError, KeyboardInterrupt):
        print()
        return 0

    aliases = {
        "c": "correct", "correct": "correct",
        "h": "higher", "higher": "higher",
        "l": "lower", "lower": "lower",
    }
    while low <= high_now:
        guess = binary_guess(low, high_now)
        guesses += 1
        while True:
            try:
                answer = input(f"Is it {guess}? (c/h/l)> ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            if answer in aliases:
                break
            print("error: answer c, h, or l.")
        result = aliases[answer]
        if result == "correct":
            print(f"\nFound it: {guess} in {guesses_label(guesses)}.")
            print(f"Optimal worst case for 1-{high}: {optimal_bound(high)}.")
            return 0
        low, high_now = apply_response(low, high_now, guess, result)
        if low > high_now:
            print("\nThose answers are inconsistent. No number fits them all.")
            return 1
        print(f"Range narrowed to {low}-{high_now}.\n")

    print("\nThose answers are inconsistent. No number fits them all.")
    return 1


def self_test():
    checks = 0

    assert hint(50, 25) == "higher"
    assert hint(50, 75) == "lower"
    assert hint(50, 50) == "correct"
    checks += 1

    assert parse_guess("42", 1, 100) == 42
    for bad in ["abc", "0", "101", "", "1.5"]:
        try:
            parse_guess(bad, 1, 100)
            raise AssertionError(f"expected ValueError for {bad!r}")
        except ValueError:
            pass
    checks += 1

    assert apply_response(1, 100, 40, "higher") == (41, 100)
    assert apply_response(1, 100, 40, "lower") == (1, 39)
    assert apply_response(1, 100, 40, "correct") == (40, 40)
    try:
        apply_response(1, 100, 40, "sideways")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    checks += 1

    assert optimal_bound(2) == 2
    assert optimal_bound(3) == 2
    assert optimal_bound(4) == 3
    assert optimal_bound(100) == 7
    assert optimal_bound(200) == 8
    checks += 1

    for high in (2, 3, 10, 100, 200, 1000):
        bound = optimal_bound(high)
        for secret in range(1, high + 1):
            low, high_now = 1, high
            guesses = 0
            while True:
                guess = binary_guess(low, high_now)
                guesses += 1
                result = hint(secret, guess)
                if result == "correct":
                    assert guess == secret
                    break
                low, high_now = apply_response(low, high_now, guess, result)
                assert low <= high_now
            assert guesses <= bound, (high, secret, guesses, bound)
    checks += 1

    for high in (1, 2):
        assert 1 <= random.Random(3).randint(1, high) <= high
    checks += 1

    print(f"37-guess-number: self-test passed ({checks} groups)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Guess a number with higher/lower hints, or let the computer guess yours.",
    )
    ap.add_argument("--max", type=int, default=100, help="upper bound of the range (default 100)")
    ap.add_argument("--computer", action="store_true", help="computer guesses your number")
    ap.add_argument("--seed", type=int, default=None, help="seed the secret number")
    ap.add_argument("--self-test", action="store_true", help="run hint/search tests and exit")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not 2 <= args.max <= 1_000_000:
        ap.error("--max must be between 2 and 1000000")
    if args.computer:
        return computer_game(args.max)
    return player_game(args.max, args.seed)


if __name__ == "__main__":
    sys.exit(main())
