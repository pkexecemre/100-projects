# 54 - log-rotate

Rotate a log file once it reaches a size limit. Backups are numbered
(`app.log.1`, `app.log.2`, ...), the newest data is always `app.log.1`, and all
renames use `os.replace()` so a reader never sees a partially copied file.
Python 3 standard library only.

## Usage

```sh
./log_rotate.py /var/log/myapp.log --max-bytes 10M --keep 5
./log_rotate.py ./app.log --max-bytes 64K --keep 3 --dry-run
```

The file is checked, not followed: run it from cron, a logrotate hook, or after
a job. Rotation does this atomically:

1. delete backups with an index greater than or equal to `--keep`
2. move `.N-1` to `.N`, working from the highest index down
3. move the live file to `.1`
4. recreate the live file empty, preserving its permission bits

Ownership and extended attributes are not copied; run as the file owner or fix
them afterwards if needed.

## Options

- `--max-bytes SIZE` - rotate at or above this size, default `1M`; accepts
  `K`, `M`, `G` suffixes and fractional values (`1.5M`)
- `--keep N` - numbered backups to retain, default 5, minimum 1
- `--dry-run` - print the renames and removals without changing anything
- `--self-test` - run built-in rotation checks

## Exit codes

- `0` - rotated, below threshold, or dry run succeeded
- `2` - missing file, bad size, invalid `--keep`, permission error

## Test

```sh
./log_rotate.py --self-test
```

The test rotates a temporary file repeatedly, checks ordering and contents of
`app.log.1`/`app.log.2`, verifies the live file is recreated empty, that a
below-threshold run is a no-op, that `--keep` prunes old backups, and that
dry-run changes nothing.
