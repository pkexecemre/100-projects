# 80 - ip-math

CIDR arithmetic for IPv4 and IPv6 using Python's `ipaddress` module: network
and broadcast addresses, netmask/wildcard, host ranges, address counts and
classification flags.

## Usage

```console
$ ./ip_math.py 192.168.1.10/24
input          192.168.1.10/24
version        4
cidr           192.168.1.0/24
prefixlen      24
network        192.168.1.0
broadcast      192.168.1.255
netmask        255.255.255.0
wildcard       0.0.0.255
first address  192.168.1.0
last address   192.168.1.255
first host     192.168.1.1
last host      192.168.1.254
addresses      256
usable hosts   254
flags          is_private
note           input had host bits; normalized to network

$ ./ip_math.py 2001:db8::/32 --json
$ ./ip_math.py 10.0.0.0/8 192.168.0.0/24
```

Behavior:

- bare addresses are treated as single-host networks (`/32` or `/128`)
- host bits in the input are accepted and normalized, with a note in text mode
  and `"host_bits_set": true` in JSON
- IPv4 `/31` reports 2 usable hosts (point-to-point) and `/32` reports 1;
  other IPv4 prefixes report `addresses - 2`
- IPv6 has no broadcast; `broadcast`, `first_host` and `last_host` are `null`
  and usable hosts equals the total address count
- flags are the true entries among `is_private`, `is_global`, `is_loopback`,
  `is_multicast`, `is_link_local`, `is_reserved`, `is_unspecified`

JSON output is an object for one target and an array for multiple targets.

## Options

- `--json` - machine-readable output
- `--self-test` - IPv4/IPv6 edge-case checks

## Exit codes

- `0` success
- `1` invalid address, prefix out of range, or empty argument
- `2` usage error (no targets given)

## Self-test

```console
$ ./ip_math.py --self-test
self-test: all checks passed
```
