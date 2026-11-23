#!/usr/bin/env python3
"""ip-summary: show interfaces, addresses, and default routes via iproute2
JSON output, with a /proc/net fallback."""

import argparse
import fcntl
import json
import os
import socket
import struct
import subprocess
import sys

SIOCGIFADDR = 0x8915
SIOCGIFNETMASK = 0x891B


def decode_hex_ipv4(hex_address):
    return socket.inet_ntop(socket.AF_INET, bytes.fromhex(hex_address)[::-1])


def decode_hex_ipv6(hex_address):
    raw = bytes.fromhex(hex_address)
    if len(raw) != 16:
        raise ValueError("bad IPv6 address")
    return socket.inet_ntop(socket.AF_INET6, raw)


def summarize_ip_addr(data):
    interfaces = []
    for item in data or []:
        addresses = []
        for addr in item.get("addr_info", []):
            if addr.get("family") not in ("inet", "inet6") or not addr.get("local"):
                continue
            addresses.append({
                "family": addr["family"],
                "address": addr["local"],
                "prefixlen": addr.get("prefixlen"),
            })
        interfaces.append({
            "name": item.get("ifname", "?"),
            "state": str(item.get("operstate", "unknown")).lower(),
            "mtu": item.get("mtu"),
            "addresses": addresses,
        })
    return interfaces


def summarize_ip_routes(data):
    routes = []
    for item in data or []:
        if item.get("dst") != "default":
            continue
        routes.append({
            "gateway": item.get("gateway") or "-",
            "device": item.get("dev") or "-",
            "metric": item.get("metric"),
            "family": "inet6" if ":" in str(item.get("gateway", "")) else "inet",
        })
    return routes


def run_ip(*args):
    proc = subprocess.run(["ip", "-j", *args], capture_output=True, text=True,
                          timeout=5)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "ip exited %d" % proc.returncode)
    return json.loads(proc.stdout or "[]")


def load_ip():
    return {
        "interfaces": summarize_ip_addr(run_ip("addr")),
        "default_routes": summarize_ip_routes(run_ip("route")),
    }


def interface_ipv4(name):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        packed = struct.pack("256s", name[:15].encode())
        raw_addr = fcntl.ioctl(sock.fileno(), SIOCGIFADDR, packed)[20:24]
        raw_mask = fcntl.ioctl(sock.fileno(), SIOCGIFNETMASK, packed)[20:24]
        mask = struct.unpack("!I", raw_mask)[0]
        return socket.inet_ntoa(raw_addr), bin(mask).count("1")
    except OSError:
        return None
    finally:
        sock.close()


def proc_read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return ""


def parse_proc_dev(text):
    names = []
    for line in text.splitlines():
        if ":" not in line:
            continue
        name = line.split(":", 1)[0].strip()
        if not name or name.startswith("Inter-"):
            continue
        names.append(name)
    return names


def parse_if_inet6(text):
    addresses = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 6:
            continue
        try:
            address = decode_hex_ipv6(parts[0])
            prefixlen = int(parts[2], 16)
        except (ValueError, OSError):
            continue
        addresses.append({"family": "inet6", "address": address,
                          "prefixlen": prefixlen, "name": parts[5]})
    return addresses


def parse_proc_route(text):
    routes = []
    for line in text.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 8:
            continue
        iface, destination, gateway, mask, metric = (parts[0], parts[1], parts[2],
                                                     parts[7], parts[6])
        if destination != "00000000" or mask != "00000000":
            continue
        try:
            hop = decode_hex_ipv4(gateway) if gateway != "00000000" else "-"
            value = int(metric)
        except ValueError:
            continue
        routes.append({"gateway": hop, "device": iface, "metric": value,
                       "family": "inet"})
    return routes


def sysfs(path, default=None):
    value = proc_read(path).strip()
    return value if value else default


def load_proc():
    interfaces = []
    ipv6 = parse_if_inet6(proc_read("/proc/net/if_inet6"))
    for name in parse_proc_dev(proc_read("/proc/net/dev")):
        addresses = []
        ipv4 = interface_ipv4(name)
        if ipv4:
            addresses.append({"family": "inet", "address": ipv4[0],
                              "prefixlen": ipv4[1]})
        addresses.extend({"family": row["family"], "address": row["address"],
                          "prefixlen": row["prefixlen"]}
                         for row in ipv6 if row["name"] == name)
        mtu = sysfs("/sys/class/net/%s/mtu" % name)
        interfaces.append({
            "name": name,
            "state": sysfs("/sys/class/net/%s/operstate" % name, "unknown"),
            "mtu": int(mtu) if mtu and mtu.isdigit() else None,
            "addresses": addresses,
        })
    routes = parse_proc_route(proc_read("/proc/net/route"))
    if not interfaces:
        raise RuntimeError("no interfaces found in /proc/net")
    return {"interfaces": interfaces, "default_routes": routes}


def render(summary):
    lines = ["INTERFACES"]
    rows = [("NAME", "STATE", "MTU", "ADDRESSES")]
    for iface in summary["interfaces"]:
        addresses = ", ".join(
            "%s/%s" % (addr["address"], addr["prefixlen"])
            if addr["prefixlen"] is not None else addr["address"]
            for addr in iface["addresses"]
        ) or "-"
        rows.append((iface["name"], iface["state"],
                     "-" if iface["mtu"] is None else str(iface["mtu"]), addresses))
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    for row in rows:
        lines.append("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip())
    lines.append("")
    lines.append("DEFAULT ROUTES")
    if summary["default_routes"]:
        for route in summary["default_routes"]:
            metric = "" if route["metric"] is None else " metric %s" % route["metric"]
            lines.append("default via %s dev %s%s" % (
                route["gateway"], route["device"], metric))
    else:
        lines.append("none")
    return "\n".join(lines)


def self_test():
    assert decode_hex_ipv4("0101A8C0") == "192.168.1.1"
    assert decode_hex_ipv4("00000000") == "0.0.0.0"
    assert decode_hex_ipv6("fe80000000000000d8617a23798ee656") == "fe80::d861:7a23:798e:e656"
    addr_json = [
        {"ifname": "lo", "operstate": "UNKNOWN", "mtu": 65536,
         "addr_info": [{"family": "inet", "local": "127.0.0.1", "prefixlen": 8},
                       {"family": "inet6", "local": "::1", "prefixlen": 128}]},
        {"ifname": "eth0", "operstate": "UP", "mtu": 1500,
         "addr_info": [{"family": "inet", "local": "192.0.2.5", "prefixlen": 24}]},
    ]
    summary = summarize_ip_addr(addr_json)
    assert summary[0]["state"] == "unknown" and len(summary[0]["addresses"]) == 2
    assert summary[1]["addresses"][0]["address"] == "192.0.2.5"
    routes = summarize_ip_routes([
        {"dst": "default", "gateway": "192.0.2.1", "dev": "eth0", "metric": 100},
        {"dst": "192.0.2.0/24", "dev": "eth0"},
    ])
    assert routes == [{"gateway": "192.0.2.1", "device": "eth0", "metric": 100,
                       "family": "inet"}], routes
    dev = "Inter-| Receive | Transmit\n face |bytes packets\n lo: 0 0\n eth0: 10 1\n"
    assert parse_proc_dev(dev) == ["lo", "eth0"]
    v6 = "fe80000000000000d8617a23798ee656 03 40 20 80 wlp7s0\n"
    assert parse_if_inet6(v6)[0]["address"] == "fe80::d861:7a23:798e:e656"
    route_text = ("Iface Destination Gateway Flags RefCnt Use Metric Mask MTU Window IRTT\n"
                  "eth0 00000000 0101A8C0 0003 0 0 100 00000000 0 0 0\n"
                  "eth0 0001A8C0 00000000 0001 0 0 0 00FFFFFF 0 0 0\n")
    assert parse_proc_route(route_text) == [
        {"gateway": "192.168.1.1", "device": "eth0", "metric": 100, "family": "inet"}
    ]
    assert "INTERFACES" in render({"interfaces": summary, "default_routes": routes})
    print("self-test: ok (ip JSON, /proc parsers, hex decoding, rendering)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Summarize interfaces and routes.")
    ap.add_argument("--source", choices=("auto", "ip", "proc"), default="auto",
                    help="iproute2 JSON or /proc/net (default: auto)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--self-test", action="store_true", help="run offline checks")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    source = args.source
    summary = None
    if source in ("auto", "ip"):
        try:
            summary, source = load_ip(), "ip"
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
            if source == "ip":
                print("error: cannot read iproute2 state: %s" % exc, file=sys.stderr)
                return 2
            source = "proc"
    if summary is None:
        try:
            summary, source = load_proc(), "proc"
        except RuntimeError as exc:
            print("error: %s" % exc, file=sys.stderr)
            return 2

    if args.json:
        print(json.dumps({"source": source, **summary}))
    else:
        print(render(summary))
        if source == "proc":
            print("source: /proc/net (IPv4 addresses via ioctl)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
