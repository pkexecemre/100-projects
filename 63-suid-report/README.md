# 63 - suid-report

Walk one or more directory trees and report every regular file carrying the
SUID (`4000`) or SGID (`2000`) bit. Output includes symbolic and octal modes,
owner, group, and size.

Pseudo filesystems (`proc`, `sysfs`, `devtmpfs`, `tmpfs`, `cgroup2`, and
friends) are pruned using `/proc/mounts`, so scanning `/` does not descend into
kernel or container plumbing. A path you name explicitly is always scanned.

## Usage

```sh
# default roots: /usr and /opt
./suid_report.py

# scan selected trees
./suid_report.py /usr /bin /opt /srv

# machine-readable, fail if anything is found (CI/audit use)
./suid_report.py --json --fail-on-found /usr
```

Text output is a `MODE OWNER GROUP PATH` table followed by a count. JSON is
`{"roots": [...], "files_scanned": N, "findings": [...], "errors": [...]}`;
each finding has `path`, `mode`, `octal`, `owner`, `group`, `size`, `suid`,
`sgid`.

## Exit codes

| code | meaning |
|------|---------|
| 0 | scan completed |
| 1 | `--fail-on-found` and at least one SUID/SGID file exists |
| 2 | every supplied path was unusable |

Missing paths in an otherwise valid run are reported as warnings, not errors.

## Self-test

```sh
./suid_report.py --self-test
```

Builds three temporary executables (plain, SUID, SGID), checks JSON flags and
paths, and confirms a nonexistent scan root exits 2.
