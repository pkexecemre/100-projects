#!/usr/bin/env python3
"""tcp-sweep: concurrent TCP connect checks over explicit hosts, host:port
pairs, or IPv4 CIDR ranges."""

import argparse
import ipaddress
import json
import re
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor

DEFAULT_PORTS = "80,443"
MAX_PAIRS = 200000


class SpecError(ValueError):
    pass


def parse_ports(text):
    ports = set()
    for chunk in text.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            bounds = chunk.split("-")
            if len(bounds) != 2:
                raise SpecError("invalid port range %r" % chunk)
            try:
                lo, hi = int(bounds[0]), int(bounds[1])
            except ValueError:
                raise SpecError("invalid port range %r" % chunk)
            if not (1 <= lo <= hi <= 65535):
                raise SpecError("port range out of bounds: %r" % chunk)
            ports.update(range(lo, hi + 1))
        else:
            try:
                port = int(chunk)
            except ValueError:
                raise SpecError("invalid port %r" % chunk)
            if not 1 <= port <= 65535:
                raise SpecError("port out of bounds: %r" % chunk)
            ports.add(port)
    if not ports:
        raise SpecError("no ports specified")
    return sorted(ports)


def parse_target(token, default_ports):
    """Return (hosts, ports) for one target token."""
    token = token.strip()
    if not token:
        raise SpecError("empty target")
    if "/" in token:
        try:
            network = ipaddress.ip_network(token, strict=False)
        except ValueError as exc:
            raise SpecError("invalid CIDR %r: %s" % (token, exc))
        if network.version != 4:
            raise SpecError("only IPv4 CIDR ranges are supported")
        if network.num_addresses > 65536:
            raise SpecError("CIDR %r is larger than 65536 addresses" % token)
        hosts = [str(ip) for ip in network.hosts()]
        if not hosts:
            hosts = [str(network.network_address)]
        return hosts, list(default_ports)
    host, ports = token, list(default_ports)
    if token.startswith("["):
        match = re.match(r"^\[([^\]]+)\](?::(\d+))?$", token)
        if not match:
            raise SpecError("invalid bracketed target %r" % token)
        host = match.group(1)
        if match.group(2):
            ports = [int(match.group(2))]
    elif token.count(":") == 1:
        candidate, _, port_text = token.partition(":")
        if not candidate:
            raise SpecError("invalid target %r" % token)
        if not port_text.isdigit():
            raise SpecError("invalid port in target %r" % token)
        host, ports = candidate, [int(port_text)]
    if not host:
        raise SpecError("invalid target %r" % token)
    if any(ch.isspace() for ch in host):
        raise SpecError("invalid host %r" % host)
    for port in ports:
        if not 1 <= port <= 65535:
            raise SpecError("port out of bounds: %d" % port)
    return [host], ports


def build_jobs(targets, default_ports):
    jobs = []
    seen = set()
    for token in targets:
        hosts, ports = parse_target(token, default_ports)
        for host in hosts:
            for port in ports:
                key = (host, port)
                if key in seen:
                    continue
                seen.add(key)
                jobs.append(key)
    if len(jobs) > MAX_PAIRS:
        raise SpecError("refusing to scan %d pairs (limit %d)" % (len(jobs), MAX_PAIRS))
    return jobs


def check(host, port, timeout):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, ""
    except OSError as exc:
        return False, exc.strerror or str(exc)


def self_test():
    assert parse_ports("22,80-82,443") == [22, 80, 81, 82, 443]
    assert parse_ports(" 1 , 2 ") == [1, 2]
    for bad in ("", "0", "65536", "90-80", "1-", "x", "1-2-3"):
        try:
            parse_ports(bad)
        except SpecError:
            pass
        else:
            raise AssertionError("accepted bad ports %r" % bad)
    hosts, ports = parse_target("192.0.2.0/30", [80])
    assert hosts == ["192.0.2.1", "192.0.2.2"] and ports == [80]
    assert parse_target("192.0.2.9/32", [80]) == (["192.0.2.9"], [80])
    assert parse_target("example.test:2222", [80]) == (["example.test"], [2222])
    assert parse_target("[::1]:8443", [80]) == (["::1"], [8443])
    assert parse_target("::1", [443]) == (["::1"], [443])
    try:
        parse_target("example.test:https", [80])
    except SpecError:
        pass
    else:
        raise AssertionError("accepted non-numeric port")
    jobs = build_jobs(["example.test:22", "example.test:22"], [80])
    assert jobs == [("example.test", 22)], jobs
    print("self-test: ok (ports, targets, dedupe, job building)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Concurrent TCP connect sweep.")
    ap.add_argument("targets", nargs="*", help="host, host:port, or IPv4 CIDR")
    ap.add_argument("-p", "--ports", default=DEFAULT_PORTS,
                    help="ports for targets without one (default: 80,443)")
    ap.add_argument("--timeout", type=float, default=1.0, help="per connect (default: 1s)")
    ap.add_argument("--workers", type=int, default=64, help="threads (default: 64)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--self-test", action="store_true", help="run offline checks")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.targets:
        ap.error("at least one target is required")
    if args.timeout <= 0:
        ap.error("--timeout must be greater than zero")
    if not 1 <= args.workers <= 512:
        ap.error("--workers must be between 1 and 512")
    try:
        ports = parse_ports(args.ports)
        jobs = build_jobs(args.targets, ports)
    except SpecError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    if not jobs:
        print("error: no targets to scan", file=sys.stderr)
        return 2

    started = time.monotonic()
    results = []
    with ThreadPoolExecutor(max_workers=min(args.workers, len(jobs))) as pool:
        futures = [pool.submit(check, host, port, args.timeout) for host, port in jobs]
        for (host, port), future in zip(jobs, futures):
            ok, error = future.result()
            results.append({"host": host, "port": port, "open": ok, "error": error})
    elapsed = time.monotonic() - started
    opened = [r for r in results if r["open"]]

    if args.json:
        print(json.dumps({"scanned": len(results), "open": opened,
                          "elapsed_seconds": round(elapsed, 3)}))
    else:
        for item in opened:
            print("open %s:%d" % (item["host"], item["port"]))
        print("%d open of %d checked in %.2fs" % (len(opened), len(results), elapsed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
