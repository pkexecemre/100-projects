#!/usr/bin/env python3
"""Two-player Connect Four for the terminal, with a headless win-detection test."""

import argparse
import sys

ROWS = 6
COLS = 7
EMPTY = "."
PIECES = ("X", "O")


def empty_board():
    return [[EMPTY] * COLS for _ in range(ROWS)]


def drop(board, col, piece):
    """Drop a piece into a column. Returns the landing row, or None if full."""
    if not 0 <= col < COLS or piece not in PIECES:
        return None
    for row in range(ROWS - 1, -1, -1):
        if board[row][col] == EMPTY:
            board[row][col] = piece
            return row
    return None


def winner(board):
    """Return X or O when four connect, otherwise None."""
    for row in range(ROWS):
        for col in range(COLS):
            piece = board[row][col]
            if piece == EMPTY:
                continue
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                end_row = row + 3 * dr
                end_col = col + 3 * dc
                if not (0 <= end_row < ROWS and 0 <= end_col < COLS):
                    continue
                if all(board[row + i * dr][col + i * dc] == piece for i in range(4)):
                    return piece
    return None


def is_full(board):
    return all(cell != EMPTY for row in board for cell in row)


def is_draw(board):
    return is_full(board) and winner(board) is None


def render(board, message=""):
    lines = ["  " + " ".join(str(c + 1) for c in range(COLS))]
    for row in board:
        lines.append("  " + " ".join(row))
    lines.append("  " + "-" * (COLS * 2 - 1))
    if message:
        lines.append("  " + message)
    return "\n".join(lines)


def play():
    board = empty_board()
    player = "X"
    print("Connect Four - line up four. X moves first.\n")

    while True:
        print(render(board))
        print()
        try:
            text = input(f"{player} column (1-{COLS}, q to quit)> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if text.lower() in ("q", "quit"):
            return 0
        try:
            col = int(text) - 1
        except ValueError:
            print(f"error: enter a column number 1-{COLS}.\n")
            continue
        if not 0 <= col < COLS:
            print(f"error: column must be between 1 and {COLS}.\n")
            continue
        if drop(board, col, player) is None:
            print(f"error: column {col + 1} is full.\n")
            continue

        won = winner(board)
        if won:
            print(render(board, f"{won} wins!"))
            return 0
        if is_draw(board):
            print(render(board, "The board is full - it is a draw."))
            return 0
        player = "O" if player == "X" else "X"


def self_test():
    checks = 0

    board = empty_board()
    assert winner(board) is None and not is_full(board)
    checks += 1

    board = empty_board()
    for col in range(4):
        board[ROWS - 1][col] = "X"
    assert winner(board) == "X"
    board[ROWS - 1][0] = EMPTY
    assert winner(board) is None
    checks += 1

    board = empty_board()
    for row in range(ROWS - 4, ROWS):
        board[row][2] = "O"
    assert winner(board) == "O"
    checks += 1

    board = empty_board()
    for i in range(4):
        board[ROWS - 1 - i][i] = "X"
    assert winner(board) == "X"
    board = empty_board()
    for i in range(4):
        board[ROWS - 1 - i][COLS - 1 - i] = "O"
    assert winner(board) == "O"
    checks += 1

    board = empty_board()
    for col in range(3):
        board[ROWS - 1][col] = "X"
    assert winner(board) is None
    board[2][4] = "X"
    board[2][5] = "X"
    board[2][6] = "X"
    assert winner(board) is None
    checks += 1

    board = empty_board()
    assert drop(board, 0, "X") == ROWS - 1
    assert drop(board, 0, "O") == ROWS - 2
    assert board[ROWS - 1][0] == "X" and board[ROWS - 2][0] == "O"
    assert drop(board, -1, "X") is None
    assert drop(board, COLS, "X") is None
    assert drop(board, 0, "Z") is None
    for _ in range(ROWS - 2):
        drop(board, 0, "X")
    assert board[0][0] != EMPTY
    assert drop(board, 0, "O") is None
    checks += 1

    pattern = [
        "XOXOXOX",
        "XOXOXOX",
        "OXOXOXO",
        "OXOXOXO",
        "XOXOXOX",
        "XOXOXOX",
    ]
    board = [list(row) for row in pattern]
    assert winner(board) is None
    assert is_full(board)
    assert is_draw(board)
    board[0][0] = EMPTY
    assert not is_draw(board)
    checks += 1

    assert "1 2 3 4 5 6 7" in render(empty_board())
    assert render(empty_board()).count(".") == ROWS * COLS
    checks += 1

    print(f"35-connect4: self-test passed ({checks} groups)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Two-player Connect Four: drop pieces with column numbers.")
    ap.add_argument("--self-test", action="store_true", help="run win/drop logic tests and exit")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    return play()


if __name__ == "__main__":
    sys.exit(main())
