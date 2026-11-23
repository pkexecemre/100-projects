# 04-logfilter

Grep-style line filter for logs. Accepts a regex plus optional level-token and
tail filters. Reads a file when one is given, otherwise standard input. Output
is plain text; level tokens are coloured only when stdout is a terminal (or when
forced).

## Usage

```sh
./logfilter.py 'timeout' app.log
journalctl -b | ./logfilter.py 'nginx' --level error
./logfilter.py 'WARN|ERROR' app.log --tail 50
./logfilter.py 'panic' app.log --level fatal --color always | less -R
```

`--level` may be repeated. Accepted names: `trace`, `debug`, `info`, `warn`,
`warning`, `error`, `err`, `crit`, `critical`, `fatal`. Matching is on the
whole token, case-insensitive, and errors also match `ERR`; crit also matches
`CRITICAL` and `FATAL`. `--ignore-case` controls the main pattern only.
`--tail N` keeps just the last N matching lines (N=0 prints nothing).
`NO_COLOR` disables automatic colour.

## Exit codes

| code | meaning |
|------|---------|
| 0 | filter ran, whether or not lines matched |
| 1 | input file could not be opened or read |
| 2 | invalid regex, level name or option value |

## Test

`./logfilter.py --self-test` runs the selection pipeline over a fixed five-line
sample, checking level aliases, the tail window, the no-match case, colour
output and rejection of an unknown level.
