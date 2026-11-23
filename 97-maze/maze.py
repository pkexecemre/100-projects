#!/usr/bin/env python3
"""Generate a perfect maze with randomised DFS, then solve it with BFS."""
import argparse
import random
import sys
from collections import deque

DIRS = [("N", 0, -1, "S"), ("E", 1, 0, "W"), ("S", 0, 1, "N"), ("W", -1, 0, "E")]


def generate(width: int, height: int, rng: random.Random) -> list[list[dict]]:
    """Return walls[y][x] with N/E/S/W booleans; True means wall present."""
    walls = [[{"N": True, "E": True, "S": True, "W": True} for _ in range(width)]
             for _ in range(height)]
    seen = {(0, 0)}
    stack = [(0, 0)]
    while stack:
        x, y = stack[-1]
        options = [(d, x + dx, y + dy, opposite) for d, dx, dy, opposite in DIRS
                   if 0 <= x + dx < width and 0 <= y + dy < height
                   and (x + dx, y + dy) not in seen]
        if not options:
            stack.pop()
            continue
        direction, nx, ny, opposite = rng.choice(options)
        walls[y][x][direction] = False
        walls[ny][nx][opposite] = False
        seen.add((nx, ny))
        stack.append((nx, ny))
    return walls


def neighbours(x: int, y: int, walls: list[list[dict]]) -> list[tuple[int, int]]:
    height, width = len(walls), len(walls[0])
    out = []
    for direction, dx, dy, _ in DIRS:
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height and not walls[y][x][direction]:
            out.append((nx, ny))
    return out


def solve(width: int, height: int, walls: list[list[dict]]) -> list[tuple[int, int]] | None:
    start, goal = (0, 0), (width - 1, height - 1)
    previous = {start: None}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        if (x, y) == goal:
            path = []
            node = (x, y)
            while node is not None:
                path.append(node)
                node = previous[node]
            return path[::-1]
        for nxt in neighbours(x, y, walls):
            if nxt not in previous:
                previous[nxt] = (x, y)
                queue.append(nxt)
    return None


def render(width: int, height: int, walls: list[list[dict]],
           path: list[tuple[int, int]] | None) -> str:
    grid = [["#"] * (2 * width + 1) for _ in range(2 * height + 1)]
    for y in range(height):
        for x in range(width):
            grid[2 * y + 1][2 * x + 1] = " "
            if not walls[y][x]["E"] and x + 1 < width:
                grid[2 * y + 1][2 * x + 2] = " "
            if not walls[y][x]["S"] and y + 1 < height:
                grid[2 * y + 2][2 * x + 1] = " "
    if path:
        for (x, y), (nx, ny) in zip(path, path[1:]):
            grid[2 * y + 1][2 * x + 1] = "*"
            grid[2 * ny + 1][2 * nx + 1] = "*"
            grid[y + ny + 1][x + nx + 1] = "*"
        grid[1][1] = "S"
        grid[2 * height - 1][2 * width - 1] = "E"
    return "\n".join("".join(row) for row in grid)


def self_test() -> None:
    rng = random.Random(7)
    walls = generate(8, 5, rng)
    path = solve(8, 5, walls)
    assert path is not None and path[0] == (0, 0) and path[-1] == (7, 4)
    for (x, y), (nx, ny) in zip(path, path[1:]):
        assert abs(x - nx) + abs(y - ny) == 1
        direction = {(1, 0): "E", (-1, 0): "W", (0, 1): "S", (0, -1): "N"}[(nx - x, ny - y)]
        assert not walls[y][x][direction], "path crosses a wall"
    reachable = 0
    seen = {(0, 0)}
    queue = deque([(0, 0)])
    while queue:
        x, y = queue.popleft()
        reachable += 1
        for nxt in neighbours(x, y, walls):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    assert reachable == 8 * 5, f"maze not connected: {reachable}/40"
    assert generate(8, 5, random.Random(7)) == walls, "generation not deterministic"
    art = render(8, 5, walls, path).splitlines()
    assert len(art) == 11 and all(len(row) == 17 for row in art)
    print("self-test: ok (perfect 8x5 maze, BFS path, deterministic seed)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate and solve a maze (DFS carve, BFS solve).")
    ap.add_argument("--width", type=int, default=15, help="cells wide, 2-60 (default: 15)")
    ap.add_argument("--height", type=int, default=7, help="cells tall, 2-40 (default: 7)")
    ap.add_argument("--seed", type=int, help="seed for reproducible mazes")
    ap.add_argument("--no-solution", action="store_true", help="hide the solution path")
    ap.add_argument("--self-test", action="store_true", help="run internal checks and exit")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not (2 <= args.width <= 60 and 2 <= args.height <= 40):
        print("maze: width must be 2-60 and height 2-40", file=sys.stderr)
        return 2
    rng = random.Random(args.seed) if args.seed is not None else random.Random()
    walls = generate(args.width, args.height, rng)
    path = solve(args.width, args.height, walls)
    print(f"Maze {args.width}x{args.height} (seed {args.seed if args.seed is not None else 'random'})")
    print(render(args.width, args.height, walls, None if args.no_solution else path))
    if path and not args.no_solution:
        print(f"Solution length: {len(path)} cells")
    return 0


if __name__ == "__main__":
    sys.exit(main())
