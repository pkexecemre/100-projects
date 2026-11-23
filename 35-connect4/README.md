# 35 - Connect Four

Local two-player Connect Four on a 6x7 board. Players alternate dropping `X`
and `O`; the first to line up four horizontally, vertically, or diagonally
wins. A full board with no line is a draw.

`drop` and `winner` are pure board functions, and the self-test builds
horizontal, vertical, and both diagonal wins plus a draw position.

## Run

```sh
python3 connect4.py
python3 connect4.py --self-test
python3 connect4.py --help
```

## Play

Enter a column number from `1` to `7`. Pieces fall to the lowest free row in
that column. A full column is rejected without consuming a turn. `q` or Ctrl-D
quits.

```text
  1 2 3 4 5 6 7
  . . . . . . .
  . . . . . . .
  . . . . . . .
  . . . . . . .
  . . . . . . .
  X O . . . . .
  -------------
X column (1-7, q to quit)>
```

## Exit codes

- `0` win, draw, quit, or successful self-test
- `2` invalid command-line options
