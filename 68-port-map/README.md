# 68 - port-map

List listening TCP and UDP sockets and the process that owns each one. The
primary source is `ss -tulpnH`; when `ss` is unavailable or fails, the tool
falls back to `/proc/net/{tcp,tcp6,udp,udp6}` and resolves socket inodes through
`/proc/<pid>/fd`, so it still works on minimal systems.

Non-root users usually cannot see socket ownership for other users' processes;
those rows show `?` and a note. The tool is read-only.

## Usage

```sh
./port_map.py
./port_map.py --json
./port_map.py --file ss-capture.txt     # parse saved `ss -tulpnH` output
```

Text columns: `PROTO LOCAL ADDRESS PORT PID PROCESS`, sorted by port. JSON:

```json
{"source": "ss", "count": 2, "notes": [],
 "listening": [{"proto": "tcp", "state": "LISTEN", "local_address": "0.0.0.0",
                "port": 22, "pid": 456, "process": "sshd"}]}
```

The `/proc` fallback decodes IPv4 and IPv6 hex addresses. UDP connected sockets
with unusual states are ignored; normal unconnected listeners (state `07`) are
kept.

## Exit codes

| code | meaning |
|------|---------|
| 0 | table produced |
| 2 | `--file` unreadable |

## Self-test

```sh
./port_map.py --self-test
```

Parses a fixed `ss` fixture with IPv4/IPv6 SSH listeners, UDP DNS, and a socket
with no visible owner; checks ports, PIDs, process names, sort order, `/proc`
fallback shape, and the missing-file error.
