#!/usr/bin/env python3
"""Minesweeper with seedable boards, flags, and a terminal-free self-test."""

import argparse
import random
import sys


def neighbors(cell, rows, cols):
    row, col = cell
    return [
        (r, c)
        for r in range(max(0, row - 1), min(rows, row + 2))
        for c in range(max(0, col - 1), min(cols, col + 2))
        if (r, c) != cell
    ]


def make_mines(rows, cols, count, rng, safe=None):
    """Place `count` distinct mines, optionally excluding one safe cell."""
    cells = [(r, c) for r in range(rows) for c in range(cols) if (r, c) != safe]
    if count > len(cells):
        raise ValueError("not enough cells for mines")
    rng.shuffle(cells)
    return set(cells[:count])


def count_adjacent(mines, rows, cols):
    """Map every cell to its adjacent-mine count; mines map to -1."""
    counts = {}
    for r in range(rows):
        for c in range(cols):
            if (r, c) in mines:
                counts[(r, c)] = -1
            else:
                counts[(r, c)] = sum(1 for n in neighbors((r, c), rows, cols) if n in mines)
    return counts


def reveal(mines, counts, revealed, flags, cell, rows, cols):
    """Reveal a cell, flood-filling through zeroes. Returns boom, ok, or blocked."""
    if cell in flags or cell in revealed:
        return "blocked"
    if cell in mines:
        revealed.add(cell)
        return "boom"
    stack = [cell]
    while stack:
        current = stack.pop()
        if current in revealed or current in flags:
            continue
        revealed.add(current)
        if counts[current] == 0:
            for n in neighbors(current, rows, cols):
                if n not in mines and n not in revealed:
                    stack.append(n)
    return "ok"


def toggle_flag(flags, revealed, cell):
    """Toggle a flag. Returns False when the cell is already revealed."""
    if cell in revealed:
        return False
    if cell in flags:
        flags.remove(cell)
    else:
        flags.add(cell)
    return True


def is_win(mines, revealed, total_cells):
    return len(revealed) >= total_cells - len(mines)


def render(rows, cols, counts, revealed, flags, show_mines=False):
    lines = ["    " + "".join(f"{c + 1:>3}" for c in range(cols))]
    for r in range(rows):
        cells = []
        for c in range(cols):
            cell = (r, c)
            if show_mines and counts.get(cell) == -1:
                symbol = "F" if cell in flags else "*"
            elif cell in flags:
                symbol = "F"
            elif cell in revealed:
                if counts.get(cell) == -1:
                    symbol = "X"
                else:
                    value = counts.get(cell, 0)
                    symbol = "." if value == 0 else str(value)
            else:
                symbol = "#"
            cells.append(f"{symbol:>3}")
        lines.append(f"{r + 1:>3} " + "".join(cells))
    return "\n".join(lines)


def play(rows, cols, mine_count, seed):
    rng = random.Random(seed)
    mines = None
    counts = {}
    revealed = set()
    flags = set()
    total = rows * cols

    print(f"Minesweeper {rows}x{cols}, {mine_count} mines.")
    print("Commands: r ROW COL (reveal), f ROW COL (flag), q (quit).")
    print("Coordinates are 1-based. Your first reveal is always safe.\n")

    while True:
        print(render(rows, cols, counts, revealed, flags))
        print(
            f"mines {mine_count}   flags {len(flags)}   "
            f"revealed {len(revealed)}/{total - mine_count}\n"
        )
        try:
            parts = input("command> ").strip().split()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not parts:
            continue
        if parts[0] in ("q", "quit"):
            return 0
        if parts[0] in ("h", "help"):
            print("  r ROW COL  reveal a cell")
            print("  f ROW COL  place or remove a flag")
            print("  q          quit\n")
            continue
        if parts[0] not in ("r", "f") or len(parts) != 3:
            print("error: use 'r ROW COL', 'f ROW COL', or 'q'.\n")
            continue
        try:
            row = int(parts[1]) - 1
            col = int(parts[2]) - 1
        except ValueError:
            print("error: ROW and COL must be whole numbers.\n")
            continue
        if not (0 <= row < rows and 0 <= col < cols):
            print(f"error: ROW must be 1-{rows} and COL must be 1-{cols}.\n")
            continue
        cell = (row, col)

        if parts[0] == "f":
            if not toggle_flag(flags, revealed, cell):
                print("error: that cell is already revealed.\n")
            continue

        if mines is None:
            mines = make_mines(rows, cols, mine_count, rng, safe=cell)
            counts = count_adjacent(mines, rows, cols)

        result = reveal(mines, counts, revealed, flags, cell, rows, cols)
        if result == "blocked":
            print("error: that cell is flagged or already open.\n")
            continue
        if result == "boom":
            print(render(rows, cols, counts, revealed, flags, show_mines=True))
            print(f"\nBOOM. You hit a mine after opening {len(revealed) - 1} cells.")
            return 0
        if is_win(mines, revealed, total):
            print(render(rows, cols, counts, revealed, flags, show_mines=True))
            print(f"\nCleared! All {total - mine_count} safe cells opened.")
            return 0


def self_test():
    checks = 0

    assert len(neighbors((0, 0), 5, 5)) == 3
    assert len(neighbors((2, 2), 5, 5)) == 8
    assert len(neighbors((4, 4), 5, 5)) == 3
    assert (2, 2) not in neighbors((2, 2), 5, 5)
    checks += 1

    rng = random.Random(5)
    mines = make_mines(9, 9, 10, rng, safe=(4, 4))
    assert len(mines) == 10
    assert (4, 4) not in mines
    assert len(make_mines(9, 9, 10, random.Random(5), safe=(4, 4))) == len(mines)
    assert make_mines(9, 9, 10, random.Random(5)) == make_mines(9, 9, 10, random.Random(5))
    try:
        make_mines(2, 2, 4, rng, safe=(0, 0))
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    checks += 1

    mines = {(1, 1)}
    counts = count_adjacent(mines, 3, 3)
    assert counts[(1, 1)] == -1
    assert counts[(0, 0)] == 1
    assert counts[(0, 1)] == 1
    assert counts[(2, 2)] == 1
    assert counts[(0, 2)] == 1
    assert counts[(2, 0)] == 1
    assert counts[(1, 2)] == 1
    assert count_adjacent(set(), 2, 2)[(0, 0)] == 0
    checks += 1

    mines = {(0, 0)}
    counts = count_adjacent(mines, 5, 5)
    revealed = set()
    progress = set()
    flags = set()
    assert reveal(mines, counts, progress, flags, (4, 4), 5, 5) == "ok"
    assert len(progress) == 24
    assert mines not in progress
    assert reveal(mines, counts, revealed, flags, (0, 1), 5, 5) == "ok"
    assert len(revealed) == 1
    assert reveal(mines, counts, revealed, flags, (0, 0), 5, 5) == "boom"
    assert (0, 0) in revealed
    checks += 1

    revealed = {(0, 1)}
    flags = set()
    assert reveal(mines, counts, revealed, flags, (0, 1), 5, 5) == "blocked"
    assert toggle_flag(flags, revealed, (2, 2))
    assert (2, 2) in flags
    assert reveal(mines, counts, revealed, flags, (2, 2), 5, 5) == "blocked"
    assert toggle_flag(flags, revealed, (2, 2))
    assert (2, 2) not in flags
    assert not toggle_flag(flags, revealed, (0, 1))
    checks += 1

    mines = {(0, 0)}
    counts = count_adjacent(mines, 5, 5)
    revealed = {(r, c) for r in range(5) for c in range(5)} - mines
    assert is_win(mines, revealed, 25)
    revealed.discard((4, 4))
    assert not is_win(mines, revealed, 25)
    flags = {(1, 1)}
    assert not toggle_flag(flags, revealed, (0, 1))
    checks += 1

    board = render(5, 5, counts, set(), set())
    assert board.count("#") == 25
    flagged = render(5, 5, counts, set(), {(1, 1)})
    assert "F" in flagged
    lost = render(5, 5, counts, {(0, 0)}, set(), show_mines=True)
    hit = render(5, 5, counts, {(0, 0)}, set(), show_mines=False)
    assert "*" in lost and "X" in hit
    assert len(board.splitlines()) == 6
    checks += 1

    print(f"33-minesweeper: self-test passed ({checks} groups)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Terminal minesweeper with flood reveal and flags.")
    ap.add_argument("--rows", type=int, default=9, help="board rows (default 9)")
    ap.add_argument("--cols", type=int, default=9, help="board columns (default 9)")
    ap.add_argument("--mines", type=int, default=10, help="mine count (default 10)")
    ap.add_argument("--seed", type=int, default=None, help="seed mine placement")
    ap.add_argument("--self-test", action="store_true", help="run logic tests and exit")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not 2 <= args.rows <= 30:
        ap.error("--rows must be between 2 and 30")
    if not 2 <= args.cols <= 30:
        ap.error("--cols must be between 2 and 30")
    if not 1 <= args.mines < args.rows * args.cols:
        ap.error("--mines must be at least 1 and leave one safe cell")
    return play(args.rows, args.cols, args.mines, args.seed)


if __name__ == "__main__":
    sys.exit(main())
