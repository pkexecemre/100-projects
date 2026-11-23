#!/usr/bin/env python3
"""Hangman with an ASCII gallows, a built-in word list, and a headless self-test."""

import argparse
import random
import sys

MAX_WRONG = 6

WORDS = [
    "python", "terminal", "puzzle", "garden", "rocket", "harbor", "library",
    "magnet", "cactus", "wizard", "planet", "silver", "copper", "jungle",
    "breeze", "candle", "dragon", "falcon", "goblin", "island", "kitten",
    "ladder", "marble", "napkin", "orange", "pepper", "quartz", "rabbit",
    "saddle", "tiger", "umpire", "violin", "walnut", "yogurt", "zebra",
]

GALLOWS = [
    ["  +---+", "  |   |", "  |", "  |", "  |", "  |", "======="],
    ["  +---+", "  |   |", "  |   O", "  |", "  |", "  |", "======="],
    ["  +---+", "  |   |", "  |   O", "  |   |", "  |", "  |", "======="],
    ["  +---+", "  |   |", "  |   O", "  |  /|", "  |", "  |", "======="],
    ["  +---+", "  |   |", "  |   O", "  |  /|\\", "  |", "  |", "======="],
    ["  +---+", "  |   |", "  |   O", "  |  /|\\", "  |  /", "  |", "======="],
    ["  +---+", "  |   |", "  |   O", "  |  /|\\", "  |  / \\", "  |", "======="],
]


def mask(word, guesses):
    return " ".join(letter if letter in guesses else "_" for letter in word)


def wrong_letters(word, guesses):
    return sorted(letter for letter in guesses if letter not in word)


def status(word, guesses, limit=MAX_WRONG):
    if all(letter in guesses for letter in word):
        return "win"
    if len(wrong_letters(word, guesses)) >= limit:
        return "lose"
    return "playing"


def normalize_guess(text):
    letter = text.strip().lower()
    if len(letter) != 1 or not letter.isalpha() or not letter.isascii():
        raise ValueError("guess must be one ASCII letter")
    return letter


def draw(word, guesses, limit=MAX_WRONG):
    stage = min(len(wrong_letters(word, guesses)), limit)
    lines = list(GALLOWS[stage])
    lines.append("")
    lines.append("  word:  " + mask(word, guesses))
    missed = " ".join(wrong_letters(word, guesses)) or "-"
    lines.append(f"  miss:  {missed}  ({len(wrong_letters(word, guesses))}/{limit})")
    return "\n".join(lines)


def play(seed):
    rng = random.Random(seed)
    word = rng.choice(WORDS)
    guesses = set()

    print(f"Hangman - {MAX_WRONG} wrong guesses allowed. Type one letter or q.\n")
    while True:
        print(draw(word, guesses))
        print()
        state = status(word, guesses)
        if state == "win":
            print(f"You win! The word was '{word}'.")
            return 0
        if state == "lose":
            print(f"You lose. The word was '{word}'.")
            return 0
        try:
            text = input("letter> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if text.strip().lower() in ("q", "quit"):
            return 0
        try:
            letter = normalize_guess(text)
        except ValueError as exc:
            print(f"error: {exc}.\n")
            continue
        if letter in guesses:
            print(f"'{letter}' was already guessed.\n")
            continue
        guesses.add(letter)
        if letter in word:
            print(f"Good: {letter} is in the word.\n")
        else:
            print(f"Miss: {letter} is not in the word.\n")


def self_test():
    checks = 0

    assert mask("apple", set()) == "_ _ _ _ _"
    assert mask("apple", {"a", "p"}) == "a p p _ _"
    assert mask("apple", set("apple")) == "a p p l e"
    checks += 1

    word = "apple"
    assert wrong_letters(word, {"a", "z", "x"}) == ["x", "z"]
    assert wrong_letters(word, set(word)) == []
    assert status(word, set("apple")) == "win"
    assert status(word, {"z"}) == "playing"
    assert status(word, set("bcdfgh")) == "lose"
    assert status(word, set("bcdfg")) == "playing"
    checks += 1

    assert len(GALLOWS) == MAX_WRONG + 1
    assert all(len(stage) == 7 for stage in GALLOWS)
    assert "O" not in GALLOWS[0][2]
    assert "O" in GALLOWS[1][2]
    assert "/|\\" in GALLOWS[4][3]
    checks += 1

    assert len(WORDS) >= 20
    assert len(set(WORDS)) == len(WORDS)
    assert all(word.isalpha() and word.islower() and word.isascii() for word in WORDS)
    checks += 1

    for text, expected in [("A", "a"), (" z ", "z")]:
        assert normalize_guess(text) == expected
    for bad in ["", "ab", "1", "!", "  "]:
        try:
            normalize_guess(bad)
            raise AssertionError(f"expected ValueError for {bad!r}")
        except ValueError:
            pass
    checks += 1

    guesses = set()
    for letter in "python":
        guesses.add(letter)
    assert status("python", guesses) == "win"
    assert mask("python", guesses) == "p y t h o n"
    guesses = set("bcdfgj")
    assert status("python", guesses) == "lose"
    assert len(wrong_letters("python", guesses)) == 6
    checks += 1

    text = draw("python", {"p", "x"})
    assert "p _ _ _ _ _" in text and "x" in text and "(1/6)" in text
    assert draw("python", set()) == draw("python", set())
    checks += 1

    print(f"34-hangman: self-test passed ({checks} groups)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="ASCII hangman: guess the hidden word one letter at a time.")
    ap.add_argument("--seed", type=int, default=None, help="seed word selection")
    ap.add_argument("--self-test", action="store_true", help="run logic tests and exit")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    return play(args.seed)


if __name__ == "__main__":
    sys.exit(main())
