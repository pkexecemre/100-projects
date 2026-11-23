# 58 - notify

Send a desktop notification through `notify-send`, with a plain terminal
fallback when no desktop session or notification daemon is available. Python 3
standard library only.

## Usage

```sh
./notify.py "Build finished" "All 214 tests passed"
./notify.py "Disk almost full" "root at 96%" --urgency critical --app backup
./notify.py "Reminder" --expire 0 --force-terminal
```

`notify-send` is used only when it is installed and either `DISPLAY` or
`WAYLAND_DISPLAY` is set. If the tool is missing or exits non-zero, the message
is printed to stderr as:

```text
[CRITICAL] Disk almost full: root at 96%
```

The fallback deliberately writes to stderr so a script's stdout stays clean.
`--force-terminal` always takes the fallback path, which is handy in cron,
containers, and tmux sessions without a notification daemon.

## Options

- `-u, --urgency LEVEL` - `low`, `normal`, or `critical` (default `normal`)
- `-a, --app NAME` - application name shown by the daemon (default `notify`)
- `-t, --expire MS` - display timeout in milliseconds (default 5000)
- `--force-terminal` - skip `notify-send`
- `--self-test` - run built-in checks of argument building and fallback

## Exit codes

- `0` - delivered via `notify-send` or the terminal fallback
- `2` - blank title, unknown urgency, negative expiry

## Test

```sh
./notify.py --self-test
```

The test validates urgency and expiry handling, builds the `notify-send`
argument vector, and checks the fallback line (`[CRITICAL] Title: Body`) by
capturing a forced-terminal call. It never contacts a notification daemon.
