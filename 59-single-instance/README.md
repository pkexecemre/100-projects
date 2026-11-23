# 59 - single-instance

Run a command while holding an exclusive kernel `flock`, so a second copy of
the same job exits immediately instead of overlapping. The kernel releases the
lock automatically if the process dies, which avoids the classic stale-PID
deadlock. Python 3 standard library only.

## Usage

```sh
# next run exits 75 while the first is still working
./single_instance.py -- /usr/local/bin/rebuild-index

# wait up to 30 seconds for the current copy to finish
./single_instance.py --timeout 30 -- /usr/local/bin/rebuild-index

# explicit lock file shared by related jobs
./single_instance.py --lock /run/locks/report.lock --verbose -- ./report.sh
```

Without `--lock`, a path is derived from a SHA-256 of the command plus your UID
inside `$XDG_RUNTIME_DIR` or `/tmp`. The lock file records the holder's PID.
When an old file names a dead process, the next run reports it as stale and
overwrites the metadata; the `flock` itself is what actually enforces
exclusivity. `--stale SECONDS` requires the dead-PID file to be at least that
old before it is reported as reclaimed. The lock file is intentionally not
unlinked: removing lock files while other processes may still open them creates
races.

If another process holds the lock and `--timeout` is zero, the tool exits with
`75` (`EX_TEMPFAIL`). With a positive timeout it polls until the holder leaves
or the deadline passes. The child's stdout/stderr are inherited and its exit
status is returned.

## Options

- `--lock FILE` - lock path; default is derived from the command
- `--timeout SECONDS` - wait for the lock, default 0 (fail immediately)
- `--stale SECONDS` - minimum age for reporting dead-PID metadata, default 0
- `--shell` - run the joined command through `/bin/sh`
- `--verbose` - print acquisition details to stderr
- `--self-test` - run lock contention and stale-lock checks

## Exit codes

- child's status - command ran
- `75` - lock is held by another instance
- `127` - command not found
- `2` - bad arguments or unusable lock path

## Test

```sh
./single_instance.py --self-test
```

The test holds a lock, verifies that a child copy exits `75` and does not run,
releases it, verifies a second run succeeds, then writes a dead PID with an old
timestamp and asserts it is reported as a reclaimed stale lock.
