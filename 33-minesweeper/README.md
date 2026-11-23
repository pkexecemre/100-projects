# 33 - Minesweeper

A text-mode minesweeper with a configurable grid, mine counter, flood reveal,
and flags. The first reveal is guaranteed safe: mines are placed only after the
first cell is chosen, excluding it.

Logic is split into `make_mines`, `count_adjacent`, `reveal`, `toggle_flag`,
and `is_win` so the smoke test runs without any terminal input.

## Run

```sh
python3 minesweeper.py                       # 9x9, 10 mines
python3 minesweeper.py --rows 12 --cols 16 --mines 25 --seed 4
python3 minesweeper.py --self-test
python3 minesweeper.py --help
```

## Commands

Coordinates are 1-based, row first.

```text
r 3 5     reveal row 3, column 5
f 3 5     place/remove a flag
h         show help
q         quit
```

Flood reveal expands through cells with zero adjacent mines. A mine hit prints
the full board; opening every safe cell wins. Flags are advisory only and never
block a win check beyond blocking reveals on that cell.

## Exit codes

- `0` quit, win, or a lost game (game finished normally), and successful self-test
- `1` unexpected runtime failure
- `2` invalid board dimensions or mine count
