# 48 - ip-summary

One-screen network summary: interface names, state, MTU, addresses, and
default routes. Reads `ip -j addr` and `ip -j route`, and falls back to
`/proc/net` when iproute2 is unavailable.

## Usage

```sh
python3 ip_summary.py
python3 ip_summary.py --json
python3 ip_summary.py --source proc
python3 ip_summary.py --self-test
```

The `/proc/net` fallback uses `/proc/net/dev` for the interface list,
`/proc/net/if_inet6` for IPv6 addresses, `/proc/net/route` for IPv4 default
routes, and `ioctl` for IPv4 addresses/netmasks (they are not exposed in a
simple `/proc/net` file). MTU and operational state come from
`/sys/class/net/<iface>/`.

## JSON shape

```json
{"source": "ip",
 "interfaces": [{"name": "eth0", "state": "up", "mtu": 1500,
                 "addresses": [{"family": "inet", "address": "192.0.2.5",
                                "prefixlen": 24}]}],
 "default_routes": [{"gateway": "192.0.2.1", "device": "eth0",
                     "metric": 100, "family": "inet"}]}
```

## Exit codes

- `0` - summary produced
- `2` - neither iproute2 JSON nor `/proc/net` could be read
