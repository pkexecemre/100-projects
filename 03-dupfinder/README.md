# 03-dupfinder

Find duplicate files. Files are grouped by size first, and only groups with two
or more members are hashed with SHA-256, so large trees are cheap to scan. The
tool is strictly read-only: it reports what it found and never deletes.

## Usage

```sh
./dupfinder.py                      # scan the current directory
./dupfinder.py ~/Downloads ~/Pictures
./dupfinder.py /data --min-size 1M  # ignore files under one mebibyte
./dupfinder.py /data --json
```

`--min-size` takes bytes or a `K`/`M`/`G` suffix (powers of 1024). Symlinks are
skipped so they cannot fake a duplicate, and unreadable files produce a warning
on stderr without aborting the scan.

Human output is sorted by reclaimable space. JSON output has `groups` (each with
`size`, `sha256`, `files`) and a `summary` with group count, redundant file
count, and `wasted_bytes` (every copy beyond the first).

## Exit codes

| code | meaning |
|------|---------|
| 0 | scan completed (duplicates found or not) |
| 1 | a supplied path does not exist |

## Test

`./dupfinder.py --self-test` builds a temporary tree with two identical files,
one unique file and two empty files, then checks grouping at minimum sizes 1 and
0. Nothing outside the temp directory is touched.
