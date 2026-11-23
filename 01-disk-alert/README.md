# 01-disk-alert

Report local filesystem usage and flag mounts that cross warning or critical
thresholds. Reads `/proc/self/mounts`, calls `statvfs` on each mountpoint, and
skips pseudo filesystems (proc, sysfs, cgroup, tmpfs, squashfs and friends)
plus zero-sized and FUSE image mounts. Bind mounts of the same device are
counted once.

## Usage

```sh
./disk_alert.py                    # table, warn at 85%, critical at 95%
./disk_alert.py --warn 80 --crit 90
./disk_alert.py --json             # machine-readable record per filesystem
```

Thresholds accept floats. `--json` prints an object with a `filesystems` list;
each record has `mount`, `device`, `fstype`, `size`, `used`, `available`,
`percent` and `status`.

## Exit codes

| code | meaning |
|------|---------|
| 0 | every filesystem is below the warning threshold |
| 1 | at least one filesystem is at or above `--warn` |
| 2 | at least one filesystem is at or above `--crit` |
| 3 | mount table could not be read |

## Test

`./disk_alert.py --self-test` checks mount-table parsing, threshold
classification, byte formatting and a live `statvfs` call. No network needed.
