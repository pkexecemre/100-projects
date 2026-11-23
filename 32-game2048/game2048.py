#!/usr/bin/env python3
"""2048 for the terminal: ANSI board, merge rules, and a headless self-test."""

import argparse
import random
import sys

SIZE = 4
TARGET = 2048
KEYS = {
    "w": "up", "a": "left", "s": "down", "d": "right",
    "W": "up", "A": "left", "S": "down", "D": "right",
}


def empty_board():
    return [[0] * SIZE for _ in range(SIZE)]


def slide_row(row):
    """Slide and merge one row to the left. Returns (new_row, points)."""
    tiles = [value for value in row if value]
    merged = []
    points = 0
    index = 0
    while index < len(tiles):
        if index + 1 < len(tiles) and tiles[index] == tiles[index + 1]:
            value = tiles[index] * 2
            merged.append(value)
            points += value
            index += 2
        else:
            merged.append(tiles[index])
            index += 1
    merged.extend([0] * (SIZE - len(merged)))
    return merged, points


def transpose(board):
    return [list(row) for row in zip(*board)]


def flip(board):
    return [list(reversed(row)) for row in board]


def move(board, direction):
    """Apply a move. Returns (new_board, points, moved)."""
    if direction == "left":
        rows = [list(row) for row in board]
    elif direction == "right":
        rows = flip(board)
    elif direction == "up":
        rows = transpose(board)
    elif direction == "down":
        rows = flip(transpose(board))
    else:
        raise ValueError(f"unknown direction: {direction}")

    result = []
    points = 0
    for row in rows:
        new_row, gained = slide_row(row)
        result.append(new_row)
        points += gained

    if direction == "right":
        result = flip(result)
    elif direction == "up":
        result = transpose(result)
    elif direction == "down":
        result = transpose(flip(result))

    return result, points, result != board


def spawn(board, rng):
    """Place a 2 (90%) or a 4 (10%) on a random empty cell. Returns True if placed."""
    empties = [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == 0]
    if not empties:
        return False
    row, col = rng.choice(empties)
    board[row][col] = 2 if rng.random() < 0.9 else 4
    return True


def can_move(board):
    for row in board:
        if 0 in row:
            return True
    for r in range(SIZE):
        for c in range(SIZE):
            value = board[r][c]
            if r + 1 < SIZE and board[r + 1][c] == value:
                return True
            if c + 1 < SIZE and board[r][c + 1] == value:
                return True
    return False


def has_target(board):
    return any(value >= TARGET for row in board for value in row)


def new_game(rng):
    board = empty_board()
    spawn(board, rng)
    spawn(board, rng)
    return board


def render(board, score, message=""):
    lines = ["", f"  SCORE {score}    join the tiles to reach {TARGET}", ""]
    border = "+" + "------+" * SIZE
    for row in board:
        lines.append(border)
        cells = "".join(f"{value if value else '.':^6}|" for value in row)
        lines.append("|" + cells)
    lines.append(border)
    lines.append("")
    if message:
        lines.append("  " + message)
        lines.append("")
    lines.append("  move: WASD then Enter    quit: q")
    return "\n".join(lines)


def play(seed):
    rng = random.Random(seed)
    board = new_game(rng)
    score = 0
    message = ""

    while True:
        if sys.stdout.isatty():
            sys.stdout.write("\033[2J\033[H")
        print(render(board, score, message))
        if has_target(board):
            print(f"  You reached {TARGET}. You win!")
            return 0
        if not can_move(board):
            print("  No moves left. Game over.")
            return 0
        message = ""
        try:
            line = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not line:
            continue
        if line.lower() == "q":
            return 0

        direction = KEYS.get(line[0]) if len(line) == 1 else None
        if direction is None:
            message = "Use w/a/s/d or q."
            continue

        board, gained, moved = move(board, direction)
        if not moved:
            message = "That move changes nothing."
            continue
        score += gained
        if not spawn(board, rng):
            print(render(board, score, "Board full."))


def self_test():
    checks = 0

    cases = [
        ([2, 2, 4, 4], [4, 8, 0, 0], 12),
        ([2, 2, 2, 0], [4, 2, 0, 0], 4),
        ([0, 2, 0, 2], [4, 0, 0, 0], 4),
        ([4, 4, 8, 8], [8, 16, 0, 0], 24),
        ([2, 0, 2, 4], [4, 4, 0, 0], 4),
        ([2, 2, 2, 2], [4, 4, 0, 0], 8),
        ([0, 0, 0, 0], [0, 0, 0, 0], 0),
        ([8, 4, 2, 2], [8, 4, 4, 0], 4),
    ]
    for row, expected, expected_points in cases:
        result, points = slide_row(row)
        assert result == expected, (row, result, expected)
        assert points == expected_points, (row, points, expected_points)
    checks += 1

    board = [
        [2, 0, 0, 0],
        [2, 0, 0, 0],
        [4, 0, 0, 0],
        [4, 0, 0, 0],
    ]
    up, points, moved = move(board, "up")
    assert up == [[4, 0, 0, 0], [8, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    assert points == 12 and moved
    down, _, _ = move(board, "down")
    assert down == [[0, 0, 0, 0], [0, 0, 0, 0], [4, 0, 0, 0], [8, 0, 0, 0]]
    left, _, _ = move(board, "left")
    assert left == [[2, 0, 0, 0], [2, 0, 0, 0], [4, 0, 0, 0], [4, 0, 0, 0]]
    right, _, _ = move(board, "right")
    assert right == [[0, 0, 0, 2], [0, 0, 0, 2], [0, 0, 0, 4], [0, 0, 0, 4]]
    checks += 1

    same = [[2, 4, 8, 16], [2, 4, 8, 16], [2, 4, 8, 16], [2, 4, 8, 16]]
    _, _, moved = move(same, "left")
    assert not moved
    checks += 1

    full = [[2, 4, 2, 4], [4, 2, 4, 2], [2, 4, 2, 4], [4, 2, 4, 2]]
    assert not can_move(full)
    full[3][3] = 4
    assert can_move(full)
    with_zero = [[2, 4, 2, 4], [4, 2, 4, 2], [2, 4, 0, 4], [4, 2, 4, 2]]
    assert can_move(with_zero)
    checks += 1

    rng = random.Random(11)
    board = new_game(rng)
    assert sum(1 for row in board for value in row if value) == 2
    assert all(value in (0, 2, 4) for row in board for value in row)
    empties = [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == 0]
    before = sum(1 for row in board for value in row if value == 0)
    spawn(board, rng)
    assert sum(1 for row in board for value in row if value == 0) == before - 1
    checks += 1

    board = [[2, 4, 8, 16], [32, 64, 128, 256], [512, 1024, 2, 4], [8, 16, 32, 64]]
    assert not can_move(board)
    board[3][3] = 0
    assert can_move(board)
    board[3][3] = 64
    assert not spawn([list(row) for row in board], rng)
    assert not has_target(board)
    board[0][0] = 2048
    assert has_target(board)
    checks += 1

    rng = random.Random(3)
    board = new_game(rng)
    for _ in range(500):
        legal = [d for d in ("up", "down", "left", "right") if move(board, d)[2]]
        if not legal or has_target(board):
            break
        board, _, _ = move(board, rng.choice(legal))
        if not can_move(board):
            break
        if not spawn(board, rng):
            break
        assert all(value == 0 or (value & (value - 1)) == 0 for row in board for value in row)
        assert all(value >= 0 for row in board for value in row)
    checks += 1

    assert "SCORE" in render(new_game(random.Random(1)), 0)
    checks += 1

    print(f"32-game2048: self-test passed ({checks} groups)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="2048 in the terminal. Use WASD, q to quit.",
    )
    ap.add_argument("--seed", type=int, default=None, help="seed the tile generator")
    ap.add_argument("--self-test", action="store_true", help="test merge/game-over logic and exit")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    return play(args.seed)


if __name__ == "__main__":
    sys.exit(main())
