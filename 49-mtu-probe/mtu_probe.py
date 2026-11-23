#!/usr/bin/env python3
"""mtu-probe: find the path MTU with DF-set pings and a binary search."""

import argparse
import json
import re
import subprocess
import sys

IPV4_OVERHEAD = 28
IPV6_OVERHEAD = 48


class ProbeError(RuntimeError):
    pass


def ping_ok(returncode, output):
    low = output.lower()
    if any(mark in low for mark in ("frag needed", "message too long", "packet too big")):
        return False
    if re.search(r"\b1 (packets )?received\b", low):
        return True
    return returncode == 0 and bool(output.strip()) and "100% packet loss" not in low


def find_mtu(payload_min, payload_max, probe):
    """Return (largest successful payload or None, last failure text)."""
    ok, detail = probe(payload_min)
    if not ok:
        return None, detail
    best = payload_min
    low, high = payload_min + 1, payload_max
    while low <= high:
        middle = (low + high) // 2
        ok, detail = probe(middle)
        if ok:
            best = middle
            low = middle + 1
        else:
            high = middle - 1
    return best, ""


def ping_command(host, payload, timeout, ipv6):
    command = ["ping", "-n", "-c", "1"]
    if ipv6:
        command.append("-6")
    else:
        command.extend(["-M", "do"])
    command.extend(["-W", str(max(1, int(round(timeout)))), "-s", str(payload), host])
    return command


def probe_payload(host, payload, timeout, ipv6):
    command = ping_command(host, payload, timeout, ipv6)
    try:
        proc = subprocess.run(command, capture_output=True, text=True,
                              timeout=timeout + 5)
    except FileNotFoundError:
        raise ProbeError("ping executable not found")
    except subprocess.TimeoutExpired:
        return False, "ping timed out"
    output = (proc.stdout or "") + (proc.stderr or "")
    ok = ping_ok(proc.returncode, output)
    detail = "" if ok else (output.strip().splitlines() or ["no reply"])[-1]
    return ok, detail


def self_test():
    success = ("PING 192.0.2.1 (192.0.2.1) 1472(1500) bytes of data.\n"
               "1480 bytes from 192.0.2.1: icmp_seq=1 ttl=64 time=0.1 ms\n"
               "1 packets transmitted, 1 received, 0% packet loss, time 0ms\n")
    assert ping_ok(0, success)
    loss = "1 packets transmitted, 0 received, 100% packet loss, time 0ms\n"
    assert not ping_ok(1, loss)
    assert not ping_ok(1, "ping: local error: message too long, mtu=1500\n")
    assert not ping_ok(1, "From 192.0.2.1 icmp_seq=1 Frag needed and DF set (mtu = 1400)\n")
    assert "1 received" in success
    calls = []

    def simulated(payload):
        calls.append(payload)
        return payload <= 1472, "too big"

    payload, detail = find_mtu(1200, 1472, simulated)
    assert payload == 1472 and detail == "", (payload, detail)
    assert calls[0] == 1200 and len(calls) <= 12

    payload, _ = find_mtu(1200, 1472, lambda size: (size <= 1300, "too big"))
    assert payload == 1300, payload
    payload, detail = find_mtu(1200, 1472, lambda size: (False, "timeout"))
    assert payload is None and detail == "timeout"
    assert ping_command("192.0.2.1", 1400, 2, False) == [
        "ping", "-n", "-c", "1", "-M", "do", "-W", "2", "-s", "1400", "192.0.2.1"]
    assert "-6" in ping_command("2001:db8::1", 1400, 2, True)
    assert 1400 + IPV4_OVERHEAD == 1428 and 1400 + IPV6_OVERHEAD == 1448
    print("self-test: ok (ping parser, binary search, command builder)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Probe path MTU with DF pings.")
    ap.add_argument("--host", required=False, help="target host or IP")
    ap.add_argument("--min-mtu", type=int, default=576, help="search floor (default: 576)")
    ap.add_argument("--max-mtu", type=int, default=1500, help="search ceiling (default: 1500)")
    ap.add_argument("--timeout", type=float, default=2.0,
                    help="per-ping wait in seconds (default: 2)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--self-test", action="store_true", help="run offline checks")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.host:
        ap.error("--host is required")
    host = args.host.strip()
    if not host or any(ch.isspace() for ch in host) or host.startswith("-"):
        print("error: invalid host %r" % args.host, file=sys.stderr)
        return 2
    if args.timeout <= 0:
        ap.error("--timeout must be greater than zero")
    ipv6 = ":" in host
    overhead = IPV6_OVERHEAD if ipv6 else IPV4_OVERHEAD
    if not (overhead + 1 <= args.min_mtu <= args.max_mtu <= 65535):
        print("error: require %d < --min-mtu <= --max-mtu <= 65535"
              % overhead, file=sys.stderr)
        return 2

    payload_min = args.min_mtu - overhead
    payload_max = args.max_mtu - overhead
    try:
        payload, detail = find_mtu(
            payload_min, payload_max,
            lambda size: probe_payload(host, size, args.timeout, ipv6))
    except ProbeError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2

    result = {
        "host": host,
        "ipv6": ipv6,
        "path_mtu": None if payload is None else payload + overhead,
        "payload": payload,
        "overhead": overhead,
        "range_mtu": [args.min_mtu, args.max_mtu],
    }
    if args.json:
        print(json.dumps(result))
    elif payload is None:
        print("no reply from %s at %d byte payload: %s"
              % (host, payload_min, detail), file=sys.stderr)
    else:
        print("path MTU to %s: %d bytes (payload %d + %d)"
              % (host, result["path_mtu"], payload, overhead))
    return 0 if payload is not None else 1


if __name__ == "__main__":
    sys.exit(main())
