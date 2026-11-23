#!/usr/bin/env python3
"""Terminal Matrix-style rain, with plain fallback and testable frames."""
import argparse
import random
import shutil
import sys
import time

CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ@#$%&*+-=<>"
LEVEL_CODES = {0: "\x1b[1;92m", 1: "\x1b[92m", 2: "\x1b[2;32m", 9: ""}


class Rain:
    """Column-based falling streams. Frames are pure ASCII and deterministic."""

    def __init__(self, width: int, height: int, seed: int | None = None):
        if not 4 <= width <= 200:
            raise ValueError("width must be between 4 and 200")
        if not 3 <= height <= 100:
            raise ValueError("height must be between 3 and 100")
        self.width, self.height = width, height
        self.rng = random.Random(seed)
        self.drops = [self._new_drop(initial=True) for _ in range(width)]
        if not any(0 <= drop["y"] < height for drop in self.drops):
            self.drops[0]["y"] = height // 2

    def _new_drop(self, initial: bool = False) -> dict:
        return {
            "y": self.rng.randint(-self.height, self.height) if initial
                 else self.rng.randint(-self.height, -1),
            "speed": self.rng.randint(1, 2),
            "length": self.rng.randint(3, max(4, self.height // 2)),
            "head": self.rng.choice(CHARS),
        }

    def next_frame(self) -> list[list[tuple[str, int]]]:
        grid: list[list[tuple[str, int]]] = [[(" ", 9)] * self.width for _ in range(self.height)]
        for x, drop in enumerate(self.drops):
            for i in range(drop["length"]):
                y = drop["y"] - i
                if 0 <= y < self.height:
                    char = drop["head"] if i == 0 else self.rng.choice(CHARS)
                    grid[y][x] = (char, 0 if i == 0 else (1 if i < 3 else 2))
        for drop in self.drops:
            drop["y"] += drop["speed"]
            if drop["y"] - drop["length"] > self.height:
                drop.update(self._new_drop())
        return grid

    @staticmethod
    def plain(grid: list[list[tuple[str, int]]]) -> str:
        return "\n".join("".join(char for char, _ in row) for row in grid)

    @staticmethod
    def ansi(grid: list[list[tuple[str, int]]]) -> str:
        lines = []
        for row in grid:
            out, current = [], 9
            for char, level in row:
                if level != current:
                    out.append("\x1b[0m" + LEVEL_CODES[level])
                    current = level
                out.append(char)
            lines.append("".join(out) + "\x1b[0m")
        return "\n".join(lines)


def self_test() -> None:
    a = Rain(20, 8, seed=3)
    b = Rain(20, 8, seed=3)
    frames_a = [a.next_frame() for _ in range(6)]
    frames_b = [b.next_frame() for _ in range(6)]
    assert frames_a == frames_b, "frame generation is not deterministic"
    allowed = set(CHARS) | {" "}
    total_non_space = 0
    for frame in frames_a:
        text = Rain.plain(frame)
        rows = text.splitlines()
        assert len(rows) == 8 and all(len(row) == 20 for row in rows)
        assert set(text.replace("\n", "")) <= allowed
        total_non_space += sum(char != " " for char in text)
        assert len(Rain.ansi(frame).splitlines()) == 8
    assert total_non_space > 0, "generated frames are empty"
    try:
        Rain(2, 8)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid width accepted")
    print(f"self-test: ok ({len(frames_a)} deterministic frames, {len(CHARS)} glyphs)")


def main() -> int:
    size = shutil.get_terminal_size((80, 24))
    ap = argparse.ArgumentParser(description="Matrix-style terminal rain.")
    ap.add_argument("--width", type=int, default=min(size.columns, 100))
    ap.add_argument("--height", type=int, default=max(3, min(size.lines - 1, 40)))
    ap.add_argument("--frames", type=int, default=None, help="frames to render (default: 120 on a TTY, 1 when piped)")
    ap.add_argument("--delay", type=float, default=0.05, help="seconds between frames")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--no-color", action="store_true", help="plain ASCII, no ANSI escapes")
    ap.add_argument("--color", action="store_true", help="force ANSI color even when piped")
    ap.add_argument("--self-test", action="store_true", help="run internal checks and exit")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.color and args.no_color:
        print("matrix: --color and --no-color are mutually exclusive", file=sys.stderr)
        return 2
    tty = sys.stdout.isatty()
    color = (tty or args.color) and not args.no_color
    frames = args.frames if args.frames is not None else (120 if tty else 1)
    if frames < 1:
        print("matrix: frames must be >= 1", file=sys.stderr)
        return 2
    if args.delay < 0:
        print("matrix: delay must be >= 0", file=sys.stderr)
        return 2
    try:
        rain = Rain(args.width, args.height, args.seed)
    except ValueError as exc:
        print(f"matrix: {exc}", file=sys.stderr)
        return 2
    if color:
        sys.stdout.write("\x1b[?25l")
    try:
        for _ in range(frames):
            grid = rain.next_frame()
            if color:
                sys.stdout.write("\x1b[H" + Rain.ansi(grid) + "\n")
            else:
                sys.stdout.write(Rain.plain(grid) + "\n")
            sys.stdout.flush()
            if args.delay > 0 and (color or tty):
                time.sleep(args.delay)
    except KeyboardInterrupt:
        return 130
    finally:
        if color:
            sys.stdout.write("\x1b[?25h\x1b[0m\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
