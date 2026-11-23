# 08-sysinfo-json

Print a single JSON snapshot of system state, built from standard `/proc` files
and `statvfs`. Keys, list ordering and numeric rounding are fixed, so repeated
runs are easy to diff or feed to a dashboard. There is no timestamp inside the
document.

## Usage

```sh
./sysinfo_json.py                 # 200 ms CPU sample
./sysinfo_json.py --sample-ms 0   # no sleep (CPU deltas will be small)
./sysinfo_json.py --sample-ms 1000 > snapshot.json
```

The document contains:

- `loadavg`: 1/5/15 minute load, running and total process counts, last PID.
- `cpu`: user, system, idle, iowait and busy percentages measured over the
  sampling window, plus the window length.
- `memory`: total, free, available, buffers, cached, swap total and swap free in
  bytes (converted from `/proc/meminfo` kB).
- `uptime`: seconds and days since boot.
- `mounts`: real filesystems only (pseudo filesystems skipped, duplicate devices
  collapsed), sorted by mountpoint, with byte totals and use percent.
- `schema`: document version, currently `1`.

## Exit codes

| code | meaning |
|------|---------|
| 0 | snapshot printed |
| 2 | `/proc` could not be read, or invalid arguments |

## Test

`./sysinfo_json.py --self-test` collects a short sample, then checks required
keys, positive totals, percentage ranges, mount arithmetic and JSON round-trip
stability. Entirely local.
