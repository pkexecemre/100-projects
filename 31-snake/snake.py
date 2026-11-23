#!/usr/bin/env python3
"""Curses snake game with movement, growth, and collision logic split out for tests."""

import argparse
import random
import sys

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)


def new_snake(width, height):
    """Return a three-segment snake, head first, centred on the board."""
    cx, cy = width // 2, height // 2
    return [(cx, cy), (cx - 1, cy), (cx - 2, cy)]


def next_head(body, direction):
    """Cell the head would enter on the next tick."""
    hx, hy = body[0]
    return hx + direction[0], hy + direction[1]


def hits_wall(head, width, height):
    return not (0 <= head[0] < width and 0 <= head[1] < height)


def hits_self(head, body, growing=False):
    """A move into the tail is legal unless the snake is growing this tick."""
    segments = body if growing else body[:-1]
    return head in segments


def advance(body, direction, food, width, height):
    """Move the snake one tick.

    Returns (new_body, ate, dead). On death the original body is returned.
    """
    head = next_head(body, direction)
    ate = food is not None and head == food
    if hits_wall(head, width, height) or hits_self(head, body, growing=ate):
        return list(body), False, True
    new_body = [head] + list(body)
    if not ate:
        new_body.pop()
    return new_body, ate, False


def place_food(body, width, height, rng):
    """Pick a random empty cell, or None when the board is full."""
    occupied = set(body)
    free = [(x, y) for y in range(height) for x in range(width) if (x, y) not in occupied]
    return rng.choice(free) if free else None


def draw(board, stdscr, body, food, score):
    """Paint one frame into the curses window."""
    board.erase()
    board.border()
    if food is not None:
        board.addstr(food[1] + 1, food[0] + 1, "@")
    for index, (x, y) in enumerate(body):
        board.addstr(y + 1, x + 1, "O" if index == 0 else "o")
    board.refresh()
    stdscr.addstr(0, 1, f" SNAKE  score:{score}  arrows/WASD  q:quit ")
    stdscr.refresh()


def play(stdscr, width, height, seed):
    import curses

    rows, cols = stdscr.getmaxyx()
    if rows < height + 4 or cols < width + 4:
        stdscr.nodelay(False)
        stdscr.addstr(0, 0, f"Terminal too small: need {width + 4}x{height + 4}.")
        stdscr.addstr(1, 0, "Press any key to quit.")
        stdscr.refresh()
        stdscr.getch()
        return

    try:
        curses.curs_set(0)
    except curses.error:
        pass
    stdscr.nodelay(True)
    stdscr.timeout(110)
    board = curses.newwin(height + 2, width + 2, 1, 1)
    rng = random.Random(seed)
    body = new_snake(width, height)
    food = place_food(body, width, height, rng)
    direction = RIGHT
    pending = RIGHT
    score = 0

    while True:
        ch = stdscr.getch()
        if ch in (ord("q"), ord("Q"), 27):
            return
        if ch in (curses.KEY_UP, ord("w"), ord("W")):
            pending = UP
        elif ch in (curses.KEY_DOWN, ord("s"), ord("S")):
            pending = DOWN
        elif ch in (curses.KEY_LEFT, ord("a"), ord("A")):
            pending = LEFT
        elif ch in (curses.KEY_RIGHT, ord("d"), ord("D")):
            pending = RIGHT

        if (pending[0], pending[1]) != (-direction[0], -direction[1]):
            direction = pending
        body, ate, dead = advance(body, direction, food, width, height)
        if dead:
            draw(board, stdscr, body, food, score)
            stdscr.nodelay(False)
            stdscr.addstr(0, 1, f" GAME OVER  score:{score}  press any key ")
            stdscr.refresh()
            stdscr.getch()
            return
        if ate:
            score += 1
            food = place_food(body, width, height, rng)
            if food is None:
                draw(board, stdscr, body, food, score)
                stdscr.addstr(0, 1, " YOU WIN - board full  press any key ")
                stdscr.refresh()
                stdscr.nodelay(False)
                stdscr.getch()
                return
        draw(board, stdscr, body, food, score)


def run_game(width, height, seed):
    try:
        import curses
    except ImportError:
        print("error: this Python has no curses module", file=sys.stderr)
        return 1
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        print("error: snake needs an interactive terminal (try --self-test)", file=sys.stderr)
        return 1
    try:
        curses.wrapper(play, width, height, seed)
    except KeyboardInterrupt:
        pass
    return 0


def self_test():
    checks = 0

    body = new_snake(10, 8)
    assert body == [(5, 4), (4, 4), (3, 4)], body
    checks += 1

    assert next_head(body, RIGHT) == (6, 4)
    assert next_head(body, LEFT) == (4, 4)
    checks += 1

    moved, ate, dead = advance(body, RIGHT, (19, 0), 10, 8)
    assert moved == [(6, 4), (5, 4), (4, 4)] and not ate and not dead
    checks += 1

    grown, ate, dead = advance(body, RIGHT, (6, 4), 10, 8)
    assert grown == [(6, 4), (5, 4), (4, 4), (3, 4)] and ate and not dead
    checks += 1

    _, _, dead = advance([(9, 3), (8, 3)], RIGHT, None, 10, 8)
    assert dead
    _, _, dead = advance([(4, 0), (4, 1)], UP, None, 10, 8)
    assert dead
    checks += 1

    tail_chase = [(2, 2), (2, 3), (2, 4), (1, 4), (1, 3), (1, 2)]
    moved, _, dead = advance(tail_chase, LEFT, None, 8, 8)
    assert not dead and moved[0] == (1, 2)
    _, _, dead = advance(tail_chase, LEFT, (1, 2), 8, 8)
    assert dead
    checks += 1

    rng = random.Random(4)
    body = new_snake(12, 9)
    food = place_food(body, 12, 9, rng)
    assert food not in body
    assert place_food([(x, y) for y in range(2) for x in range(2)], 2, 2, rng) is None
    checks += 1

    body = new_snake(12, 9)
    food = place_food(body, 12, 9, rng)
    directions = (UP, DOWN, LEFT, RIGHT)
    for _ in range(400):
        body, ate, dead = advance(body, rng.choice(directions), food, 12, 9)
        if dead:
            body = new_snake(12, 9)
            food = place_food(body, 12, 9, rng)
        elif ate:
            food = place_food(body, 12, 9, rng)
        assert len(set(body)) == len(body)
        assert all(0 <= x < 12 and 0 <= y < 9 for x, y in body)
    checks += 1

    print(f"31-snake: self-test passed ({checks} groups)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Curses snake. Move with arrows or WASD, q quits.",
    )
    ap.add_argument("--width", type=int, default=20, help="board width in cells (default 20)")
    ap.add_argument("--height", type=int, default=14, help="board height in cells (default 14)")
    ap.add_argument("--seed", type=int, default=None, help="seed the food generator")
    ap.add_argument("--self-test", action="store_true", help="run logic tests and exit")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not 8 <= args.width <= 60:
        ap.error("--width must be between 8 and 60")
    if not 6 <= args.height <= 30:
        ap.error("--height must be between 6 and 30")
    return run_game(args.width, args.height, args.seed)


if __name__ == "__main__":
    sys.exit(main())
