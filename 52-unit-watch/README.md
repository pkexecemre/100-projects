# 52 - unit-watch

Poll one or more systemd units with `systemctl is-active`, print the initial
state of each unit, and log only state changes with ISO-8601 timestamps. Useful
as a tiny foreground watchdog when you do not want journal noise. Python 3
standard library only.

## Usage

```sh
./unit_watch.py sshd.service
./unit_watch.py --interval 2 nginx.service postgresql.service
./unit_watch.py --once sshd.service
./unit_watch.py --interval 10 --log ~/unit-states.log sshd.service
```

Example output:

```text
[2026-11-23T21:20:01+03:00] sshd.service: initial active
[2026-11-23T21:22:15+03:00] sshd.service: active -> failed
```

If `systemctl` is not installed the state is reported as `unavailable`; calls
that fail or time out are reported as `unknown`. States are compared as plain
strings, so a transition into and out of `activating` is visible too.

Polling uses `systemctl is-active <unit>` directly and does not require root.
`Ctrl-C` stops the loop cleanly.

## Options

- `--interval SECONDS` - poll period, default 5, may be fractional
- `--once` - print each unit's current state once and exit
- `--log FILE` - append the same lines to a file (parent directories created)
- `--self-test` - exercise change detection with a fake state source

## Exit codes

- `0` - normal exit, `--once` completed, or interrupted with `Ctrl-C`
- `2` - bad arguments or an unusable `--log` path

## Test

```sh
./unit_watch.py --self-test
```

The test feeds a scripted sequence of states through `watch()` and asserts two
transitions, correct timestamps format, and matching log file contents. It does
not call `systemctl`.
