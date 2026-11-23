#!/usr/bin/env python3
"""Tic-tac-toe with an unbeatable minimax AI, two-player mode, and self-test."""

import argparse
import random
import sys

LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)


def new_board():
    return [" "] * 9


def other(player):
    return "O" if player == "X" else "X"


def winner(board):
    for a, b, c in LINES:
        if board[a] != " " and board[a] == board[b] == board[c]:
            return board[a]
    return None


def available(board):
    return [index for index, value in enumerate(board) if value == " "]


def is_full(board):
    return not available(board)


def minimax(board, player, ai, depth=0):
    """Score a position from the AI's point of view; faster wins score higher."""
    won = winner(board)
    if won == ai:
        return 10 - depth
    if won:
        return depth - 10
    moves = available(board)
    if not moves:
        return 0
    if player == ai:
        best = -100
        for move in moves:
            board[move] = player
            best = max(best, minimax(board, other(player), ai, depth + 1))
            board[move] = " "
        return best
    best = 100
    for move in moves:
        board[move] = player
        best = min(best, minimax(board, other(player), ai, depth + 1))
        board[move] = " "
    return best


def best_move(board, player):
    """Return the minimax-optimal cell for `player`, or None on a full board."""
    moves = available(board)
    if not moves:
        return None
    best_score = -100
    choice = moves[0]
    for move in moves:
        board[move] = player
        score = minimax(board, other(player), player, 1)
        board[move] = " "
        if score > best_score:
            best_score = score
            choice = move
    return choice


def render(board):
    cells = [board[i] if board[i] != " " else str(i + 1) for i in range(9)]
    lines = []
    for row in range(3):
        lines.append(f" {cells[row * 3]} | {cells[row * 3 + 1]} | {cells[row * 3 + 2]} ")
        if row < 2:
            lines.append("---+---+---")
    return "\n".join(lines)


def finish(board):
    won = winner(board)
    print(render(board))
    if won:
        print(f"\n{won} wins!")
    else:
        print("\nIt is a draw.")
    return 0


def play(mode):
    board = new_board()
    player = "X"
    ai = "O" if mode == "ai" else None
    print("Tic-tac-toe. Enter a cell number 1-9, or q to quit.\n")

    while True:
        print(render(board))
        print()
        if player == ai:
            move = best_move(board, ai)
            board[move] = ai
            print(f"AI plays cell {move + 1}.\n")
        else:
            try:
                text = input(f"{player} cell (1-9, q)> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            if text.lower() in ("q", "quit"):
                return 0
            try:
                move = int(text) - 1
            except ValueError:
                print("error: enter a whole number from 1 to 9.\n")
                continue
            if not 0 <= move < 9:
                print("error: cell must be between 1 and 9.\n")
                continue
            if board[move] != " ":
                print("error: that cell is already taken.\n")
                continue
            board[move] = player

        if winner(board) or is_full(board):
            return finish(board)
        player = other(player)


def self_test():
    checks = 0

    board = new_board()
    assert winner(board) is None and not is_full(board)
    assert available(board) == list(range(9))
    checks += 1

    for line in LINES:
        board = new_board()
        for cell in line:
            board[cell] = "X"
        assert winner(board) == "X", line
    checks += 1

    board = ["X", "X", "O", "O", "X", "X", "X", "O", "O"]
    assert winner(board) is None
    assert is_full(board)
    checks += 1

    board = ["X", "X", " ", " ", " ", " ", " ", " ", " "]
    assert best_move(board, "X") == 2
    board = ["X", "X", " ", " ", "O", " ", " ", " ", " "]
    assert best_move(board, "O") == 2
    board = ["O", "O", " ", "X", "X", " ", " ", " ", " "]
    assert best_move(board, "O") == 2
    checks += 1

    board = new_board()
    assert minimax(board, "X", "X") == 0
    assert best_move(board, "X") in (0, 2, 4, 6, 8)
    full = ["X"] * 9
    assert best_move(full, "O") is None
    checks += 1

    rng = random.Random(9)
    ai_wins = 0
    draws = 0
    for _ in range(60):
        board = new_board()
        turn = "X"
        while not winner(board) and not is_full(board):
            if turn == "O":
                move = best_move(board, "O")
            else:
                move = rng.choice(available(board))
            board[move] = turn
            turn = other(turn)
        result = winner(board)
        assert result != "X"
        if result == "O":
            ai_wins += 1
        else:
            draws += 1
    assert ai_wins + draws == 60
    assert ai_wins > 0
    checks += 1

    art = render(new_board())
    assert "1 | 2 | 3" in art and "4 | 5 | 6" in art and "7 | 8 | 9" in art
    assert art.count("+") == 4
    checks += 1

    print(f"36-tic-tac-toe: self-test passed ({checks} groups, AI won {ai_wins}/60)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Tic-tac-toe against minimax or a second player.")
    ap.add_argument("--mode", choices=("ai", "2p"), default="ai", help="ai (default) or 2p")
    ap.add_argument("--self-test", action="store_true", help="run rule and AI tests, then exit")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    return play(args.mode)


if __name__ == "__main__":
    sys.exit(main())
