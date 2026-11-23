# 45 - listeners

Show listening TCP and UDP sockets. Primary source is `ss -H -tulpn`; when
`ss` is missing or fails, the tool parses `/proc/net/tcp`, `tcp6`, `udp`, and
`udp6` directly. Each socket is classified by binding address.

## Usage

```sh
python3 listeners.py
python3 listeners.py --json
python3 listeners.py --source proc
python3 listeners.py --self-test
```

Columns: protocol, local address, port, process (from `ss`; unavailable in
`/proc` mode), and exposure:

- `all` - bound to `0.0.0.0`, `::`, or `*`, reachable on every interface
- `loopback` - bound to `127.0.0.0/8`, `::1`, or localhost
- `specific` - bound to a particular interface address

`ss -p` can only resolve process names for sockets owned by the current user;
root usually sees all of them. The `/proc/net` fallback cannot map inodes to
process names, so it prints `-`.

## Exit codes

- `0` - socket table read successfully (possibly empty)
- `2` - neither `ss` nor `/proc/net` could be read
