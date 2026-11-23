# 38 - Memory

A text-grid memory game. Cards are letter labels in pairs; flip two per turn
and keep matching pairs face up. The grid is seeded on request, so the same
shuffle can be replayed.

Deck creation, shuffling, matching, and the win condition are pure functions
covered by `--self-test`.

## Run

```sh
python3 memory.py                      # 4x4, 8 pairs
python3 memory.py --rows 2 --cols 6 --seed 3
python3 memory.py --self-test
python3 memory.py --help
```

## Play

Cards are numbered row by row. Enter one number per prompt:

```text
    1   2   3   4
 1 [ 1][ 2][ 3][ 4]
 2 [ 5][ 6][ 7][ 8]
 3 [ 9][10][11][12]
 4 [13][14][15][16]

card 1 (1-16, q)> 3
card 2 (1-16, q)> 11
```

A matched pair stays revealed; a miss flips both back after the turn. Turns
count pair attempts; the ideal score is one turn per pair. `q` or Ctrl-D quits.

## Exit codes

- `0` solved, quit, or successful self-test
- `2` odd/oversized grid or other invalid options
