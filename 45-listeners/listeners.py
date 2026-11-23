#!/usr/bin/env python3
"""listeners: list listening TCP/UDP sockets and classify their exposure."""

import argparse
import json
import os
import re
import socket
import subprocess
import sys

PROC_RE = re.compile(r'\("([^"]+)"')


def split_endpoint(token):
    token = token.strip()
    if token.startswith("["):
        host, _, port = token[1:].partition("]:")
    else:
        host, _, port = token.rpartition(":")
    return host.strip("[]"), port


def classify_exposure(host):
    name = host.split("%", 1)[0].strip("[]").strip()
    if name in ("0.0.0.0", "::", "*", ""):
        return "all"
    if name == "::1" or name.startswith("127.") or name == "localhost":
        return "loopback"
    return "specific"


def dedupe(rows):
    seen = set()
    result = []
    for row in rows:
        key = (row["proto"], row["local"], row["port"], row["process"])
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def parse_ss(text):
    rows = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 5 or parts[0] not in ("tcp", "tcp6", "udp", "udp6"):
            continue
        host, port = split_endpoint(parts[4])
        if not port.isdigit():
            continue
        match = PROC_RE.search(line)
        rows.append({
            "proto": parts[0],
            "local": host,
            "port": int(port),
            "process": match.group(1) if match else "-",
            "exposure": classify_exposure(host),
        })
    return sorted(dedupe(rows), key=lambda row: (row["port"], row["proto"]))


def decode_proc_address(hex_address, ipv6):
    raw = bytes.fromhex(hex_address)
    if ipv6:
        if len(raw) != 16:
            raise ValueError("bad IPv6 address length")
        raw = b"".join(raw[i:i + 4][::-1] for i in range(0, 16, 4))
        return socket.inet_ntop(socket.AF_INET6, raw)
    if len(raw) != 4:
        raise ValueError("bad IPv4 address length")
    return socket.inet_ntop(socket.AF_INET, raw[::-1])


def parse_proc_table(text, proto):
    rows = []
    for line in text.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 4 or ":" not in parts[1]:
            continue
        if proto.startswith("tcp") and parts[3] != "0A":
            continue
        hex_address, _, hex_port = parts[1].partition(":")
        try:
            host = decode_proc_address(hex_address, proto.endswith("6"))
            port = int(hex_port, 16)
        except (ValueError, OSError):
            continue
        if not 1 <= port <= 65535:
            continue
        rows.append({"proto": proto, "local": host, "port": port,
                     "process": "-", "exposure": classify_exposure(host)})
    return rows


def load_ss():
    proc = subprocess.run(["ss", "-H", "-tulpn"], capture_output=True,
                          text=True, timeout=10)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "ss exited %d" % proc.returncode)
    return parse_ss(proc.stdout)


def load_proc():
    rows = []
    for proto in ("tcp", "tcp6", "udp", "udp6"):
        path = os.path.join("/proc/net", proto)
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                rows.extend(parse_proc_table(handle.read(), proto))
        except OSError:
            continue
    if not rows:
        raise RuntimeError("no sockets found in /proc/net")
    return sorted(dedupe(rows), key=lambda row: (row["port"], row["proto"]))


def render(rows):
    header = ("PROTO", "LOCAL", "PORT", "PROCESS", "EXPOSURE")
    table = [header] + [(r["proto"], r["local"], str(r["port"]), r["process"],
                         r["exposure"]) for r in rows]
    widths = [max(len(row[i]) for row in table) for i in range(len(header))]
    lines = ["  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip()
             for row in table]
    exposed = sum(1 for row in rows if row["exposure"] == "all")
    lines.append("")
    lines.append("%d listeners, %d bound to all interfaces" % (len(rows), exposed))
    return "\n".join(lines)


def self_test():
    sample = "\n".join([
        'tcp   LISTEN 0      4096         0.0.0.0:22        0.0.0.0:*    users:(("sshd",pid=1,fd=3))',
        'tcp   LISTEN 0      4096            [::]:22           [::]:*    users:(("sshd",pid=1,fd=4))',
        'tcp   LISTEN 0      511        127.0.0.53%lo:53        0.0.0.0:*    users:(("systemd-resolve",pid=2,fd=5))',
        'udp   UNCONN 0      0            127.0.0.1:323       0.0.0.0:*    users:(("chronyd",pid=3,fd=6))',
    ])
    rows = parse_ss(sample)
    assert len(rows) == 4, rows
    assert {r["port"]: r["process"] for r in rows}[323] == "chronyd"
    by_port = {(r["local"], r["port"]): r["exposure"] for r in rows}
    assert by_port[("0.0.0.0", 22)] == "all"
    assert by_port[("::", 22)] == "all"
    assert by_port[("127.0.0.53%lo", 53)] == "loopback"
    assert classify_exposure("192.0.2.5") == "specific"
    assert classify_exposure("::1") == "loopback"

    proc_tcp = "\n".join([
        "  sl  local_address rem_address   st tx_queue:rx_queue tr:tm->when retrnsmt uid timeout inode",
        "   0: 0100007F:0016 00000000:0000 0A 00000000:00000000 00:00000000 00000000 0 0 1",
        "   1: 0100007F:9C40 0100007F:0016 01 00000000:00000000 00:00000000 00000000 0 0 2",
    ])
    parsed = parse_proc_table(proc_tcp, "tcp")
    assert parsed == [{"proto": "tcp", "local": "127.0.0.1", "port": 22,
                       "process": "-", "exposure": "loopback"}], parsed
    ipv6 = parse_proc_table(
        "h\n 0: 00000000000000000000000001000000:0016 00000000000000000000000000000000:0000 0A 0 0 0 0 0 0",
        "tcp6")
    assert ipv6[0]["local"] == "::1" and ipv6[0]["port"] == 22, ipv6
    assert "listeners" in render(rows)
    print("self-test: ok (ss parsing, /proc parsing, exposure, rendering)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="List listening sockets.")
    ap.add_argument("--source", choices=("auto", "ss", "proc"), default="auto",
                    help="where to read sockets (default: ss, then /proc/net)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--self-test", action="store_true", help="run offline checks")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    source = args.source
    rows = None
    if source in ("auto", "ss"):
        try:
            rows, source = load_ss(), "ss"
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            if source == "ss":
                print("error: cannot read ss: %s" % exc, file=sys.stderr)
                return 2
            source = "proc"
    if rows is None:
        try:
            rows, source = load_proc(), "proc"
        except RuntimeError as exc:
            print("error: cannot read listeners: %s" % exc, file=sys.stderr)
            return 2

    exposed = sum(1 for row in rows if row["exposure"] == "all")
    if args.json:
        print(json.dumps({"source": source, "count": len(rows),
                          "exposed": exposed, "listeners": rows}))
    else:
        print(render(rows))
        if source == "proc":
            print("source: /proc/net (process names unavailable)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
