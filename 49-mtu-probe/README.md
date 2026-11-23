# 49 - mtu-probe

Find the path MTU by sending single ICMP packets with the IPv4 Don't Fragment
bit set and binary-searching the largest payload that gets a reply. Uses the
system `ping` command.

## Usage

```sh
python3 mtu_probe.py --host 192.0.2.1
python3 mtu_probe.py --host 192.0.2.1 --min-mtu 1200 --max-mtu 9000
python3 mtu_probe.py --host 2001:db8::1 --timeout 3
python3 mtu_probe.py --host 192.0.2.1 --json
python3 mtu_probe.py --self-test
```

The search floor is 576 and the ceiling 1500 by default, so a result of 1500
means "at least 1500" (raise `--max-mtu` to test jumbo paths). IPv4 runs
`ping -M do`; IPv6 hosts are detected by `:` and use `ping -6` without the DF
flag (IPv6 has no DF bit). MTU is payload plus 28 bytes for IPv4 and 48 bytes
for IPv6.

The largest payload that succeeds is reported. If even `--min-mtu` fails, the
tool exits `1`; a too-large reply containing `Frag needed` or
`message too long` is treated as proof that the probed size exceeds the path.

## Exit codes

- `0` - path MTU found
- `1` - no reply at the minimum MTU (host unreachable or filtering ICMP)
- `2` - bad flags, missing `ping`, or ping process failure
