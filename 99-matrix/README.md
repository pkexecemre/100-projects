# 99-matrix

A Matrix-style digital rain for the terminal. Each column is a falling stream
with its own speed and length; the leading glyph is bright, the next two are
mid-green and the rest fade into dim green. Frames are generated as plain ASCII
first, so they are deterministic and testable without a terminal.

## Usage

```sh
./matrix.py                          # animate until the frame budget ends
./matrix.py --frames 60 --delay 0.04
./matrix.py --seed 7 --width 60 --height 20
./matrix.py --no-color --frames 3    # plain ASCII frames
./matrix.py --color --frames 2       # ANSI even when piped
./matrix.py --self-test
```

On a TTY the script hides the cursor, homes it with ANSI escapes and restores it
on exit (including Ctrl-C, exit code 130). When output is piped it defaults to
one plain frame; pass `--frames` explicitly for more. `--no-color` forces plain
output. Width is limited to 4-200 and height to 3-100.

## Exit codes

- `0` success, including `--self-test`
- `1` bad flag or non-integer argument (argparse)
- `2` invalid dimensions, frame count or delay
- `130` interrupted with Ctrl-C
