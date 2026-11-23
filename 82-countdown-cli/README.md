# 82 - countdown-cli

A tiny countdown timer. It prints the remaining time in place on a terminal,
then announces completion through `notify-send` when that command exists. On a
headless or minimal system the timer still works and rings the terminal bell as
a fallback.

## Usage

```sh
python3 countdown.py --seconds 90
python3 countdown.py --minutes 25 --label "Tea break"
python3 countdown.py --minutes 5 --quiet --no-notify
python3 countdown.py --self-test
```

`--seconds` and `--minutes` are mutually exclusive; one is required. Durations
must be between 0 and 86400 seconds. When output is redirected, progress lines
are suppressed and only the final `Done:` line is written, which keeps logs
clean. `--quiet` suppresses all normal output, and `--no-notify` disables the
desktop notification.

## Exit codes

- `0` timer completed normally
- `2` usage error: missing or negative duration, both duration flags, bad value

The self-test checks duration formatting, instant completion, quiet mode, and
confirmed that no notification is attempted when disabled.
