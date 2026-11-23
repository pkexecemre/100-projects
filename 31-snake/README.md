# 31 - Snake

A curses snake game. Eat `@`, grow, and avoid the walls and your own body.
The board is a bordered grid with a live score; a full board is a win.

Movement, growth, wall collision, and self-collision live in small pure
functions (`advance`, `next_head`, `hits_self`, `place_food`) so the smoke test
can exercise them without starting curses.

## Run

```sh
python3 snake.py                 # 20x14 board
python3 snake.py --width 30 --height 20 --seed 7
python3 snake.py --self-test     # no terminal needed
python3 snake.py --help
```

## Controls

- Arrow keys or `WASD` to steer, `q` or `Esc` to quit.
- The snake cannot reverse directly into itself.
- Each food adds one point and one segment.

The game needs a real terminal at least `width+4` by `height+4` in size and
refuses to start otherwise (exit 1) instead of crashing in curses.

## Exit codes

- `0` finished normally (quit, game over, win, or successful self-test)
- `1` no curses module or no interactive terminal
- `2` invalid command-line options
