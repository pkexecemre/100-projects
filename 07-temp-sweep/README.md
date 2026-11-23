# 07-temp-sweep

Find old files in temporary directories and report how much space they use.
Only regular files owned by your own uid are considered, so a shared `/tmp` is
safe to inspect: other users' files and symlinks are ignored. Nothing is deleted
unless `--apply` is given.

## Usage

```sh
./temp_sweep.py                          # scan /tmp for files older than 7 days
./temp_sweep.py /tmp /var/tmp --days 3
./temp_sweep.py /tmp --days 30 --json
./temp_sweep.py /tmp --days 7 --apply    # asks for confirmation
./temp_sweep.py /tmp --days 7 --apply --yes
```

Age is based on mtime with a strict `>` comparison. `--apply` prints the count
and total size and asks `[y/N]`; a non-interactive run without `--yes` refuses
rather than deleting. Deletion failures are listed per file and the remaining
files are still attempted. Directories are never removed.

## Exit codes

| code | meaning |
|------|---------|
| 0 | scan completed, or deletion completed with no failures |
| 1 | at least one file could not be deleted |
| 2 | invalid argument, missing directory, or unsafe non-tty `--apply` |

## Test

`./temp_sweep.py --self-test` creates an old file and a fresh file in a temp
directory, checks age and uid filtering, then deletes through the same code path
and confirms only the old file disappeared.
