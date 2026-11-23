#!/usr/bin/env python3
"""Map listening TCP/UDP ports to processes via ss, with a /proc fallback."""

import argparse
import json
import os
import re
import shutil
import socket
import stat
import struct
import subprocess
import sys


def split_endpoint(text):
    if text.startswith("["):
        addr, _, port = text.rpartition("]:")
        return addr.lstrip("["), port
    addr, _, port = text.rpartition(":")
    return addr, port


def parse_ss(text):
    rows = []
    for line in text.splitlines():
        parts = line.split(None, 6)
        if len(parts) < 5 or parts[0] not in ("tcp", "udp"):
            continue
        proto, state, local = parts[0], parts[1], parts[4]
        if proto == "tcp" and state != "LISTEN":
            continue
        if proto == "udp" and state not in ("UNCONN", "LISTEN"):
            continue
        users = parts[6] if len(parts) > 6 else ""
        addr, port = split_endpoint(local)
        try:
            port_num = int(port)
        except ValueError:
            continue
        pid = None
        process = "?"
        names = re.findall(r'\("([^"]+)",pid=(\d+)', users)
        if names:
            process = ",".join(name for name, _ in names)
            pid = int(names[0][1])
        rows.append({"proto": proto, "state": state, "local_address": addr,
                     "port": port_num, "pid": pid, "process": process})
    return dedupe(rows)


def dedupe(rows):
    seen = set()
    out = []
    for row in rows:
        key = (row["proto"], row["local_address"], row["port"], row["pid"])
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return sorted(out, key=lambda row: (row["port"], row["proto"], row["local_address"]))


def decode_address(hex_addr, version):
    addr_hex, port_hex = hex_addr.split(":")
    port = int(port_hex, 16)
    raw = bytes.fromhex(addr_hex)
    if version == 4:
        ip = socket.inet_ntoa(struct.pack("<I", int(addr_hex, 16)))
    else:
        words = [raw[idx:idx + 4][::-1] for idx in range(0, 16, 4)]
        ip = socket.inet_ntop(socket.AF_INET6, b"".join(words))
    return ip, port


def socket_owners():
    owners = {}
    try:
        pids = [name for name in os.listdir("/proc") if name.isdigit()]
    except OSError:
        return owners
    for pid in pids:
        fd_dir = "/proc/%s/fd" % pid
        try:
            fds = os.listdir(fd_dir)
        except OSError:
            continue
        for fd in fds:
            try:
                target = os.readlink(os.path.join(fd_dir, fd))
            except OSError:
                continue
            match = re.fullmatch(r"socket:\[(\d+)\]", target)
            if not match:
                continue
            try:
                with open("/proc/%s/comm" % pid, encoding="utf-8", errors="replace") as fh:
                    comm = fh.read().strip()
            except OSError:
                comm = "?"
            owners.setdefault(match.group(1), (int(pid), comm))
    return owners


def parse_proc():
    owners = socket_owners()
    rows = []
    tables = [("tcp", "/proc/net/tcp", 4), ("tcp", "/proc/net/tcp6", 6),
              ("udp", "/proc/net/udp", 4), ("udp", "/proc/net/udp6", 6)]
    for proto, path, version in tables:
        try:
            fh = open(path, encoding="utf-8")
        except OSError:
            continue
        with fh:
            next(fh, None)
            for line in fh:
                fields = line.split()
                if len(fields) < 10:
                    continue
                state = fields[3].upper()
                if proto == "tcp" and state != "0A":
                    continue
                if proto == "udp" and state not in ("07", "0A"):
                    continue
                try:
                    addr, port = decode_address(fields[1], version)
                except (ValueError, OSError):
                    continue
                pid, process = owners.get(fields[9], (None, "?"))
                rows.append({"proto": proto, "state": "LISTEN" if proto == "tcp" else "UNCONN",
                             "local_address": addr, "port": port,
                             "pid": pid, "process": process})
    return dedupe(rows)


def gather(path):
    notes = []
    if path:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return parse_ss(fh.read()), "file", notes
    if shutil.which("ss"):
        try:
            proc = subprocess.run(["ss", "-tulpnH"], capture_output=True,
                                  text=True, timeout=15,
                                  env={**os.environ, "LC_ALL": "C"})
            if proc.returncode == 0:
                return parse_ss(proc.stdout), "ss", notes
            notes.append("ss failed: %s" % (proc.stderr.strip() or "exit %d" % proc.returncode))
        except (OSError, subprocess.TimeoutExpired) as exc:
            notes.append("ss failed: %s" % exc)
    else:
        notes.append("ss not installed")
    return parse_proc(), "proc", notes


def self_test():
    import subprocess
    import tempfile

    script = os.path.abspath(__file__)
    fixture = """\
tcp LISTEN 0 128 0.0.0.0:22 0.0.0.0:* users:(("sshd",pid=456,fd=3))
tcp LISTEN 0 128 [::]:22 [::]:* users:(("sshd",pid=456,fd=4))
udp UNCONN 0 0 127.0.0.53:53 0.0.0.0:* users:(("systemd-resolve",pid=123,fd=13))
tcp LISTEN 0 128 127.0.0.1:631 0.0.0.0:* 
"""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "ss.txt")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(fixture)
        result = subprocess.run([sys.executable, script, "--file", path, "--json"],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["source"] == "file" and report["count"] == 4, report
        sshd = [row for row in report["listening"] if row["port"] == 22]
        assert len(sshd) == 2 and all(row["pid"] == 456 and row["process"] == "sshd"
                                      for row in sshd)
        dns = [row for row in report["listening"] if row["port"] == 53][0]
        assert dns["process"] == "systemd-resolve" and dns["proto"] == "udp"
        assert any(row["port"] == 631 and row["pid"] is None
                   for row in report["listening"])
        assert parse_proc() == sorted(parse_proc(), key=lambda row: (
            row["port"], row["proto"], row["local_address"]))
        result = subprocess.run([sys.executable, script, "--file",
                                 os.path.join(tmp, "absent.txt")],
                                capture_output=True, text=True)
        assert result.returncode == 2
    print("self-test: PASS")


def main():
    ap = argparse.ArgumentParser(
        description="Map listening ports to processes using ss, fallback /proc/net.")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--file", help="parse saved `ss -tulpnH` output")
    ap.add_argument("--self-test", action="store_true", help="run built-in smoke test")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    try:
        rows, source, notes = gather(args.file)
    except OSError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    report = {"source": source, "listening": rows, "count": len(rows), "notes": notes}
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("%-5s %-18s %-6s %-7s %s" %
              ("PROTO", "LOCAL ADDRESS", "PORT", "PID", "PROCESS"))
        for row in rows:
            print("%-5s %-18.18s %-6d %-7s %s" %
                  (row["proto"], row["local_address"], row["port"],
                   "-" if row["pid"] is None else row["pid"], row["process"]))
        print("\n%d listening socket(s) (source: %s)" % (len(rows), source))
        if source == "proc" and any(row["pid"] is None for row in rows):
            print("note: process names for sockets owned by other users need root")
        for note in notes:
            print("note: %s" % note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
