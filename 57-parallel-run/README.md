# 57 - parallel-run

Run shell commands listed in a file with a bounded number of concurrent workers,
capture stdout, stderr and exit codes, then print a grouped report and a
summary. Python 3 standard library only (`concurrent.futures`).

## Usage

```sh
./parallel_run.py jobs.txt
./parallel_run.py jobs.txt --jobs 8 --timeout 30
./parallel_run.py jobs.txt --jobs 2 --quiet
```

`jobs.txt` holds one command per line. Blank lines and lines starting with `#`
are ignored. Commands run through `/bin/sh`:

```text
# smoke checks
echo starting
test -f /etc/hostname
curl -fsS http://127.0.0.1:8080/health
```

Results are printed in file order even though completion order varies:

```text
[1] echo starting
    ok exit=0 0.003s
    | starting
[2] test -f /etc/hostname
    ok exit=0 0.002s
summary: 2 commands, 2 ok, 0 failed
```

A timeout kills the command's shell and records exit code `124`. Exit codes
from commands are reported as-is. `--quiet` hides captured output but still
prints status lines and the summary.

## Options

- `--jobs N` - maximum concurrent commands, default 4, minimum 1
- `--timeout SECONDS` - per-command limit; omit for no limit
- `--quiet` - do not echo captured stdout/stderr
- `--self-test` - run built-in concurrency and timeout checks

## Exit codes

- `0` - every command exited 0
- `1` - at least one command failed or timed out
- `2` - missing/empty command file or bad arguments

## Test

```sh
./parallel_run.py --self-test
```

The test writes a small command file, checks comment/blank-line parsing, runs
three commands with `--jobs 2`, asserts exit codes `[0, 3, 0]` and captured
output, and verifies that a sleeping command is reported as `124` under a short
timeout.
