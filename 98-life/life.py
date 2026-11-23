#!/usr/bin/env python3
"""Conway's Game of Life with built-in patterns and a toroidal grid."""
import argparse
import random
import sys
import time

PATTERNS = {
    "blinker": [(0, 0), (1, 0), (2, 0)],
    "toad": [(1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1)],
    "glider": [(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)],
    "block": [(0, 0), (1, 0), (0, 1), (1, 1)],
    "pulsar": (
        [(x, 0) for x in (2, 3, 4, 8, 9, 10)]
        + [(x, y) for y in (2, 3, 4) for x in (0, 5, 7, 12)]
        + [(x, 5) for x in (2, 3, 4, 8, 9, 10)]
        + [(x, 7) for x in (2, 3, 4, 8, 9, 10)]
        + [(x, y) for y in (8, 9, 10) for x in (0, 5, 7, 12)]
        + [(x, 12) for x in (2, 3, 4, 8, 9, 10)]
    ),
}
PATTERNS["pulsar"] = list(dict.fromkeys(PATTERNS["pulsar"]))


def place(pattern: str, width: int, height: int, seed: int | None) -> set[tuple[int, int]]:
    if pattern == "random":
        rng = random.Random(seed)
        return {(x, y) for y in range(height) for x in range(width) if rng.random() < 0.28}
    cells = PATTERNS[pattern]
    max_x = max(x for x, _ in cells) + 1
    max_y = max(y for _, y in cells) + 1
    ox, oy = (width - max_x) // 2, (height - max_y) // 2
    return {((x + ox) % width, (y + oy) % height) for x, y in cells}


def step(cells: set[tuple[int, int]], width: int, height: int) -> set[tuple[int, int]]:
    counts: dict[tuple[int, int], int] = {}
    for x, y in cells:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    pos = ((x + dx) % width, (y + dy) % height)
                    counts[pos] = counts.get(pos, 0) + 1
    survivors = {c for c in cells if counts.get(c, 0) in (2, 3)}
    births = {c for c, n in counts.items() if n == 3 and c not in cells}
    return survivors | births


def render(cells: set[tuple[int, int]], width: int, height: int) -> str:
    return "\n".join("".join("#" if (x, y) in cells else "." for x in range(width))
                     for y in range(height))


def self_test() -> None:
    blinker = {(1, 2), (2, 2), (3, 2)}
    vertical = {(2, 1), (2, 2), (2, 3)}
    assert step(blinker, 5, 5) == vertical
    assert step(vertical, 5, 5) == blinker, "blinker does not oscillate with period 2"
    block = {(1, 1), (2, 1), (1, 2), (2, 2)}
    assert step(block, 5, 5) == block, "block is not stable"
    toad = {(1, 1), (2, 1), (3, 1), (0, 2), (1, 2), (2, 2)}
    assert step(step(toad, 6, 6), 6, 6) == toad, "toad is not period 2"
    pulsar = set(PATTERNS["pulsar"])
    assert step(step(step(pulsar, 17, 17), 17, 17), 17, 17) == pulsar, "pulsar is not period 3"
    assert len(place("block", 10, 8, None)) == 4
    assert place("random", 10, 8, 4) == place("random", 10, 8, 4)
    art = render(blinker, 5, 5).splitlines()
    assert len(art) == 5 and all(len(row) == 5 for row in art)
    print("self-test: ok (blinker, block, toad and pulsar verified)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Conway's Game of Life.")
    ap.add_argument("--pattern", choices=[*PATTERNS, "random"], default="glider")
    ap.add_argument("--generations", type=int, default=10, help="steps to simulate (default: 10)")
    ap.add_argument("--frames", type=int, help="how many generations to print (default: all)")
    ap.add_argument("--width", type=int, default=24)
    ap.add_argument("--height", type=int, default=16)
    ap.add_argument("--seed", type=int, help="seed for --pattern random")
    ap.add_argument("--delay", type=float, default=0.0, help="seconds between frames")
    ap.add_argument("--self-test", action="store_true", help="run internal checks and exit")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not (5 <= args.width <= 120 and 5 <= args.height <= 60):
        print("life: width must be 5-120 and height 5-60", file=sys.stderr)
        return 2
    if args.generations < 0:
        print("life: generations must be >= 0", file=sys.stderr)
        return 2
    available = args.generations + 1
    frames = available if args.frames is None else args.frames
    if frames < 1:
        print("life: frames must be >= 1", file=sys.stderr)
        return 2
    frames = min(frames, available)
    cells = place(args.pattern, args.width, args.height, args.seed)
    for generation in range(args.generations + 1):
        if generation < frames:
            print(f"Generation {generation} ({len(cells)} alive)")
            print(render(cells, args.width, args.height))
            if generation < frames - 1:
                print()
            if args.delay > 0 and generation < frames - 1:
                time.sleep(args.delay)
        if generation < args.generations:
            cells = step(cells, args.width, args.height)
    return 0


if __name__ == "__main__":
    sys.exit(main())
