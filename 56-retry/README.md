# 56 - retry

Run a command and retry it on failure with exponential backoff and optional
jitter. Reports every attempt with a timestamp, then exits with the command's
status. Python 3 standard library only.

## Usage

```sh
./retry.py --max 5 -- curl -fsS https://example.invalid/health
./retry.py --max 4 --base 0.2 --factor 2 --jitter 0.3 -- ./deploy.sh
./retry.py --shell --max 3 -- 'grep -q ready /tmp/state && echo ok'
```

Attempt 1 runs immediately. Before attempt `k+1` the tool sleeps:

```text
delay = min(max_delay, base * factor ** (k - 1))
delay = max(0, delay +- jitter * delay)
```

With the defaults (`base 0.5`, `factor 2`, `jitter 0.1`, `max_delay 30`) waits
are roughly 0.5s, 1s, 2s, 4s, ... with a small random spread. Jitter is useful
when several jobs fail and retry together.

Every attempt is logged, including the elapsed time and exit status. The final
line reports either success after N attempts or that the tool is giving up.
The command's stdout and stderr are passed through directly.

## Options

- `--max N` - total attempts including the first, default 3, minimum 1
- `--base SECONDS` - first backoff delay, default 0.5
- `--factor X` - multiplier per attempt, default 2, minimum 1
- `--max-delay SECONDS` - delay ceiling, default 30
- `--jitter FRACTION` - random +/- fraction of each delay, 0 to 1, default 0.1
- `--shell` - run the joined command through `/bin/sh`
- `--self-test` - run backoff and retry tests

## Exit codes

- `0` - an attempt succeeded
- command status - all attempts failed; the last status is returned
- `126` / `127` - command could not be executed / was not found
- `2` - bad arguments

## Test

```sh
./retry.py --self-test
```

The test uses a temporary flaky script that fails twice then succeeds, asserts
the attempt sequence, checks that an always-failing command stops at the limit,
and verifies backoff capping and the jitter range.
