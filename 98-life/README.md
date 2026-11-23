# 98-life

Conway's Game of Life on a toroidal (wrap-around) grid, with built-in patterns:
`blinker`, `toad`, `glider`, `block`, `pulsar`, and `random`. The default run
shows a glider drifting across a 24x16 board.

## Usage

```sh
./life.py
./life.py --pattern pulsar --generations 12 --frames 4
./life.py --pattern random --seed 42 --width 40 --height 20
./life.py --pattern blinker --generations 4 --delay 0.2
./life.py --self-test
```

`--generations` is the number of simulation steps after the initial state.
`--frames` caps how many generations are printed (default: all of them, i.e.
generations + 1) without changing the simulation. `#` is alive, `.` is dead.
`--delay` pauses between printed frames for a simple animation.

## Exit codes

- `0` success, including `--self-test`
- `1` bad flag or non-integer argument (argparse)
- `2` board dimensions, generations or frames outside supported limits
