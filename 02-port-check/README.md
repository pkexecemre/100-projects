# 02-port-check

TCP connect scanner for one host. Ports can be given as a comma list, ranges,
or a mix. Probes run concurrently with a bounded thread pool, each with its own
connect timeout, and results are printed in a sorted table.

## Usage

```sh
./port_check.py 127.0.0.1 22,80,443
./port_check.py example.com 1-1024 --timeout 1 --workers 64
./port_check.py localhost 5432,6379-6381 --json
```

`--json` prints `{"host": ..., "results": [{"port", "open", "ms", "note"}]}`.
Closed ports include a note (`refused`, `timeout`, `dns: ...`, and so on).
Name resolution happens once per probe, so a bad host is reported as a DNS
failure for every port rather than crashing.

## Exit codes

| code | meaning |
|------|---------|
| 0 | all probed ports accepted a connection |
| 1 | at least one port was closed or errored |
| 2 | invalid arguments or port specification |

## Test

`./port_check.py --self-test` binds a loopback listener and checks one open and
one closed port locally. It also exercises port-spec parsing and rejection of
invalid ranges. No external network is used.
