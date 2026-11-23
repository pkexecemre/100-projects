# 97-maze

Generate a perfect maze (exactly one path between any two cells) using
randomised depth-first search carving, then solve it with breadth-first search.
`S` marks the start, `E` the goal, `*` the solution path and `#` the walls.

## Usage

```sh
./maze.py
./maze.py --width 21 --height 11 --seed 42
./maze.py --no-solution --seed 1
./maze.py --self-test
```

The output grid is `(2 * width + 1)` columns by `(2 * height + 1)` rows. Width
is limited to 2-60 cells and height to 2-40 cells. Without `--seed` the maze is
random each run; with a seed the walls and solution are reproducible.

## Exit codes

- `0` success, including `--self-test`
- `1` bad flag or non-integer dimension (argparse)
- `2` dimensions outside the supported limits
