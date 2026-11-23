# 60 - timeit

Run a command and report wall-clock time plus user and system CPU time from
`resource.getrusage(RUSAGE_CHILDREN)`, its exit code, and optional repeat
statistics. Python 3 standard library only.

## Usage

```sh
./timeit.py -- python3 -c 'sum(range(10_000_000))'
./timeit.py --repeat 5 --warmup 1 -- ./bench.sh
./timeit.py --repeat 3 --json -- sleep 0.1
```

Example:

```text
run 1: exit 0 wall 0.031s user 0.029s sys 0.002s
run 2: exit 0 wall 0.030s user 0.028s sys 0.002s
results: n=2 mean=0.031s min=0.030s max=0.031s stdev=0.001s total=0.061s
cpu: user=0.057s sys=0.004s
```

Wall time comes from `time.perf_counter()`. CPU deltas are taken around each
child wait, so they cover the command and anything it waited for. Warmup runs
are executed but excluded from the reported statistics; the count is shown.
`--json` prints one object with `runs`, `summary`, and `warmup` instead of the
human report. Statistics use the `statistics` module; stdev is 0 for one run.

For a single run the exit code is the command's. With repeats, the tool exits
with the first non-zero status observed, so a flaky benchmark still fails the
caller. Commands that cannot start are reported as `127` (not found) or `126`
(execution error) with a note in the JSON error field.

## Options

- `--repeat N` - timed runs, default 1, minimum 1
- `--warmup N` - untimed runs before measurement, default 0
- `--json` - machine-readable output
- `--shell` - run the joined command through `/bin/sh`
- `--self-test` - run timing, failure, and statistics checks

## Exit codes

- `0` - all measured runs exited 0
- first non-zero command status - some measured run failed
- `2` - bad arguments

## Test

```sh
./timeit.py --self-test
```

The test times a short sleep, checks a failing command returns 3, checks a
missing binary returns 127, verifies summary count/min/max/exit codes and the
single-run stdev, and exercises the text reporter.
