# 64 - world-writable

Find world-writable files and directories under one or more paths. Directories
protected by the sticky bit (`/tmp`-style, mode `1777`) are reported separately
and skipped by default, because sticky semantics prevent other users from
deleting or replacing entries there.

## Usage

```sh
# default roots: /tmp and /var/tmp
./world_writable.py

# scan a web root and list sticky directories too
./world_writable.py --include-sticky /var/www /tmp

# machine-readable
./world_writable.py --json /srv /home
```

Pseudo filesystems are pruned via `/proc/mounts`. Only regular files and real
directories are listed; symlinks and sockets/FIFOs are ignored. Each finding
carries `path`, `type`, `mode`, `octal`, `owner`, `group`, `sticky`. Sticky
directories are included only with `--include-sticky`, and are marked
`[sticky]` in the text table.

## Exit codes

| code | meaning |
|------|---------|
| 0 | scan completed (findings are normal output) |
| 2 | no scan path was usable |

Unreadable subdirectories are reported as warnings on stderr and do not abort
the scan.

## Self-test

```sh
./world_writable.py --self-test
```

Creates a 0777 directory, a 1777 directory, a 0666 file, and a 0644 file,
then verifies default filtering, sticky handling, and the JSON flags.
