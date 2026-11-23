# 42 - tcp-sweep

Concurrent TCP connect checks. Targets are explicit: hostnames, `host:port`
pairs, or IPv4 CIDR ranges. Nothing is scanned unless you name it.

## Usage

```sh
python3 tcp_sweep.py example.test
python3 tcp_sweep.py example.test:22 db.test:5432 --ports 80,443
python3 tcp_sweep.py 192.0.2.0/28 --ports 22,80,443 --workers 32
python3 tcp_sweep.py example.test:443 --timeout 2 --json
python3 tcp_sweep.py --self-test
```

`--ports` (default `80,443`) applies to targets without an embedded port.
CIDR ranges use `ipaddress` and are capped at 65536 addresses; the total work
is capped at 200000 host/port pairs. Connect attempts use `--timeout` (default
1s) and run in a bounded thread pool.

## Output

Text mode prints one `open host:port` line per successful connection and a
summary. JSON mode emits `scanned`, `open` (host, port, error), and
`elapsed_seconds`. Closed and filtered ports are counted but not listed.

## Exit codes

- `0` - sweep completed (regardless of how many ports were open)
- `2` - bad target, bad port list, bad flags, or nothing to scan
