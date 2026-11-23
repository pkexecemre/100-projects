# 32 - 2048

A terminal implementation of 2048. Each move slides all tiles in one direction;
equal neighbours merge once and award their combined value. New tiles are 2
(90%) or 4 (10%). The game ends at 2048 (win) or when no slide or merge remains.

The board is drawn with ASCII and plain ANSI clear-screen escapes, so it works
in any terminal. Tile rules are pure functions (`slide_row`, `move`,
`can_move`) with a headless smoke test.

## Run

```sh
python3 game2048.py
python3 game2048.py --seed 42
python3 game2048.py --self-test
python3 game2048.py --help
```

## Controls

- `w` `a` `s` `d` then Enter.
- `q` quits (also Ctrl-D).
- Merges give points equal to the new tile value.

Input is line based by design: it redraws a clean board after every command and
works over plain pipes as well. The self-test path never touches the terminal.

## Exit codes

- `0` quit, win, game over, or successful self-test
- `2` invalid command-line options
