# 69 - integrity-baseline

Snapshot a directory tree into a JSON baseline (sha256, size, mode, mtime per
regular file), then compare later. Comparison reports three buckets:

- **added** - present now, absent from the baseline
- **removed** - present in the baseline, gone now
- **changed** - sha256, size, or mode differs (mtime is recorded but not compared,
  because ordinary copies update it)

Symlinks and special files are skipped. `.git`, `__pycache__`, and
`node_modules` are excluded. The baseline file is skipped if it lives inside the
tree, so a snapshot does not hash itself.

## Usage

```sh
./integrity_baseline.py --create /var/lib/baselines/etc.json /etc

./integrity_baseline.py --compare /var/lib/baselines/etc.json
./integrity_baseline.py --compare baseline.json --json
./integrity_baseline.py --compare baseline.json --root /mnt/snapshot
```

The stored `root` is used unless `--root` overrides it, which is useful after
restoring a backup at a different path. Writes happen only with `--create`;
`--compare` is read-only.

## Exit codes

| code | meaning |
|------|---------|
| 0 | baseline created, or comparison is clean |
| 1 | comparison found added/removed/changed files |
| 2 | bad arguments, invalid baseline, or unreadable tree |

## Self-test

```sh
./integrity_baseline.py --self-test
```

Creates a three-file baseline, verifies a clean comparison, then mutates, adds,
and deletes files to assert exact added/removed/changed detection and exit 1.
