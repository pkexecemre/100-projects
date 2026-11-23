#!/usr/bin/env python3
"""CIDR math for IPv4 and IPv6: network, masks, ranges and host counts."""

import argparse
import ipaddress
import json
import sys


def describe(text):
    spec = text.strip()
    if not spec:
        raise ValueError("empty network")
    try:
        net = ipaddress.ip_network(spec, strict=False)
    except ValueError as exc:
        raise ValueError(f"invalid network {spec!r}: {exc}")

    host_bits = False
    try:
        ipaddress.ip_network(spec, strict=True)
    except ValueError:
        host_bits = True

    last_address = net.network_address + (net.num_addresses - 1)
    if net.version == 4:
        broadcast = str(net.broadcast_address)
        if net.prefixlen >= 31:
            first_host, last_host = str(net.network_address), str(last_address)
        else:
            first_host = str(net.network_address + 1)
            last_host = str(last_address - 1)
        usable = net.num_addresses if net.prefixlen >= 31 else net.num_addresses - 2
    else:
        broadcast = None
        first_host = last_host = None
        usable = net.num_addresses

    flags = [name for name in
             ("is_private", "is_global", "is_loopback", "is_multicast",
              "is_link_local", "is_reserved", "is_unspecified")
             if getattr(net, name, False)]
    return {
        "input": spec,
        "version": net.version,
        "cidr": str(net),
        "prefixlen": net.prefixlen,
        "network": str(net.network_address),
        "broadcast": broadcast,
        "netmask": str(net.netmask),
        "wildcard": str(net.hostmask),
        "first_address": str(net.network_address),
        "last_address": str(last_address),
        "first_host": first_host,
        "last_host": last_host,
        "num_addresses": net.num_addresses,
        "usable_hosts": usable,
        "host_bits_set": host_bits,
        "flags": flags,
    }


def show(payload):
    rows = [
        ("input", payload["input"]),
        ("version", payload["version"]),
        ("cidr", payload["cidr"]),
        ("prefixlen", payload["prefixlen"]),
        ("network", payload["network"]),
        ("broadcast", payload["broadcast"] or "-"),
        ("netmask", payload["netmask"]),
        ("wildcard", payload["wildcard"]),
        ("first address", payload["first_address"]),
        ("last address", payload["last_address"]),
        ("first host", payload["first_host"] or "-"),
        ("last host", payload["last_host"] or "-"),
        ("addresses", payload["num_addresses"]),
        ("usable hosts", payload["usable_hosts"]),
        ("flags", ", ".join(payload["flags"]) or "-"),
    ]
    if payload["host_bits_set"]:
        rows.append(("note", "input had host bits; normalized to network"))
    for key, value in rows:
        print(f"{key:<14} {value}")


def self_test():
    small = describe("192.168.1.10/24")
    assert small["cidr"] == "192.168.1.0/24" and small["version"] == 4
    assert small["network"] == "192.168.1.0"
    assert small["broadcast"] == "192.168.1.255"
    assert small["netmask"] == "255.255.255.0"
    assert small["wildcard"] == "0.0.0.255"
    assert small["first_host"] == "192.168.1.1"
    assert small["last_host"] == "192.168.1.254"
    assert small["usable_hosts"] == 254
    assert small["num_addresses"] == 256
    assert small["host_bits_set"] is True
    assert "is_private" in small["flags"]

    assert describe("10.0.0.0/31")["usable_hosts"] == 2
    assert describe("10.0.0.0/31")["last_host"] == "10.0.0.1"
    assert describe("10.0.0.7/32")["usable_hosts"] == 1
    assert describe("10.0.0.7/32")["host_bits_set"] is False
    bare = describe("8.8.8.8")
    assert bare["cidr"] == "8.8.8.8/32" and bare["usable_hosts"] == 1

    v6 = describe("2001:db8::1/32")
    assert v6["version"] == 6 and v6["cidr"] == "2001:db8::/32"
    assert v6["broadcast"] is None and v6["first_host"] is None
    assert v6["num_addresses"] == 2 ** 96
    assert v6["usable_hosts"] == 2 ** 96
    assert describe("2001:db8::/126")["last_address"] == "2001:db8::3"
    assert describe("::/0")["num_addresses"] == 2 ** 128

    for bad in ("", "192.168.1.0/33", "not-an-ip", "2001:db8::/129"):
        try:
            describe(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted invalid network {bad!r}")
    print("self-test: all checks passed")


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--self-test" in argv:
        self_test()
        return 0

    ap = argparse.ArgumentParser(
        description="CIDR network math for IPv4 and IPv6.",
        epilog="Examples: ip_math.py 192.168.1.10/24 | ip_math.py 2001:db8::/32 --json",
    )
    ap.add_argument("cidrs", nargs="+", metavar="CIDR",
                    help="address or network, with optional /prefix")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    payloads = []
    try:
        for spec in args.cidrs:
            payloads.append(describe(spec))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payloads[0] if len(payloads) == 1 else payloads, indent=2))
    else:
        for index, payload in enumerate(payloads):
            if index:
                print()
            show(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
