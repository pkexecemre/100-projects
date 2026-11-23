#!/usr/bin/env python3
"""Rock-paper-scissors: best-of-N series with hints-free scoring and self-test."""

import argparse
import random
import sys

MOVES = ("rock", "paper", "scissors")
BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
ALIASES = {
    "r": "rock", "rock": "rock",
    "p": "paper", "paper": "paper",
    "s": "scissors", "scissors": "scissors",
}


def winner(player, computer):
    """Return player, computer, or tie."""
    if player == computer:
        return "tie"
    return "player" if BEATS[player] == computer else "computer"


def parse_move(text):
    key = text.strip().lower()
    if key not in ALIASES:
        raise ValueError("move must be rock, paper, or scissors")
    return ALIASES[key]


def target_wins(best_of):
    return best_of // 2 + 1


def series_over(player_wins, computer_wins, best_of):
    target = target_wins(best_of)
    return player_wins >= target or computer_wins >= target


def play(best_of, seed):
    rng = random.Random(seed)
    player_wins = 0
    computer_wins = 0
    ties = 0
    target = target_wins(best_of)

    print(f"Best of {best_of} - first to {target} wins. Ties do not count.")
    print("Moves: rock, paper, scissors (or r/p/s). q quits.\n")

    while not series_over(player_wins, computer_wins, best_of):
        try:
            text = input("your move> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if text.strip().lower() in ("q", "quit"):
            return 0
        try:
            player = parse_move(text)
        except ValueError as exc:
            print(f"error: {exc}.\n")
            continue

        computer = rng.choice(MOVES)
        result = winner(player, computer)
        if result == "player":
            player_wins += 1
            label = "you win"
        elif result == "computer":
            computer_wins += 1
            label = "computer wins"
        else:
            ties += 1
            label = "tie"
        print(f"you: {player:<8} computer: {computer:<8} {label}")
        print(f"score  you {player_wins} - {computer_wins} computer   ties {ties}\n")

    if player_wins > computer_wins:
        print(f"You win the series {player_wins}-{computer_wins}!")
    else:
        print(f"Computer wins the series {computer_wins}-{player_wins}.")
    print(f"Rounds: {player_wins + computer_wins + ties}, ties: {ties}.")
    return 0


def self_test():
    checks = 0

    for player in MOVES:
        assert winner(player, player) == "tie"
        for computer in MOVES:
            if computer == player:
                continue
            expected = "player" if BEATS[player] == computer else "computer"
            assert winner(player, computer) == expected, (player, computer)
    checks += 1

    assert parse_move(" R ") == "rock"
    assert parse_move("P") == "paper"
    assert parse_move("scissors") == "scissors"
    for bad in ["", "fire", "rock paper", "1"]:
        try:
            parse_move(bad)
            raise AssertionError(f"expected ValueError for {bad!r}")
        except ValueError:
            pass
    checks += 1

    assert [target_wins(n) for n in (1, 3, 5, 7, 9)] == [1, 2, 3, 4, 5]
    assert not series_over(1, 0, 3)
    assert series_over(2, 0, 3)
    assert series_over(0, 2, 3)
    assert not series_over(1, 1, 3)
    assert series_over(1, 0, 1)
    checks += 1

    rng = random.Random(12)
    player_wins = 0
    computer_wins = 0
    ties = 0
    rounds = 0
    script = ["rock", "paper", "scissors"]
    while not series_over(player_wins, computer_wins, 7):
        player = script[rounds % 3]
        computer = rng.choice(MOVES)
        result = winner(player, computer)
        if result == "player":
            player_wins += 1
        elif result == "computer":
            computer_wins += 1
        else:
            ties += 1
        rounds += 1
        assert rounds < 1000
    assert max(player_wins, computer_wins) == target_wins(7)
    assert player_wins + computer_wins + ties == rounds
    checks += 1

    assert all(winner(p, c) in ("player", "computer", "tie") for p in MOVES for c in MOVES)
    checks += 1

    print(f"39-rps: self-test passed ({checks} groups)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Best-of-N rock-paper-scissors against the computer.")
    ap.add_argument("--best-of", type=int, default=3, help="odd number of rounds (default 3)")
    ap.add_argument("--seed", type=int, default=None, help="seed the computer's choices")
    ap.add_argument("--self-test", action="store_true", help="run scoring tests and exit")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.best_of < 1 or args.best_of % 2 == 0 or args.best_of > 99:
        ap.error("--best-of must be an odd number from 1 to 99")
    return play(args.best_of, args.seed)


if __name__ == "__main__":
    sys.exit(main())
