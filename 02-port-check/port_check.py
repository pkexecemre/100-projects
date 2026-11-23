#!/usr/bin/env python3
"""Check TCP ports on a host with a bounded thread pool."""

import argparse
import json
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor


def parse_ports(spec):
    """Parse '22,80,8000-8010' into a sorted list of unique ports."""
    ports = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            raise ValueError("empty port entry")
        if "-" in chunk:
            lo_s, hi_s = chunk.split("-", 1)
            lo, hi = int(lo_s), int(hi_s)
            if lo > hi:
                raise ValueError(f"range starts above its end: {chunk}")
            if hi - lo > 65535:
                raise ValueError(f"range too wide: {chunk}")
            ports.update(range(lo, hi + 1))
        else:
            ports.add(int(chunk))
    bad = [p for p in ports if not 1 <= p <= 65535]
    if bad:
        raise ValueError(f"port out of range: {bad[0]}")
    if not ports:
        raise ValueError("no ports given")
    return sorted(ports)


def check_port(host, port, timeout):
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
        return {"port": port, "open": True,
                "ms": round((time.perf_counter() - start) * 1000, 1), "note": ""}
    except socket.timeout:
        note = "timeout"
    except socket.gaierror as exc:
        note = f"dns: {exc.strerror or exc}"
    except ConnectionRefusedError:
        note = "refused"
    except OSError as exc:
        note = exc.strerror or str(exc)
    return {"port": port, "open": False,
            "ms": round((time.perf_counter() - start) * 1000, 1), "note": note}


def render(host, results):
    lines = [f"host: {host}", f"{'PORT':>5}  {'STATE':6} {'MS':>8}  NOTE"]
    for r in results:
        state = "open" if r["open"] else "closed"
        lines.append(f"{r['port']:>5}  {state:6} {r['ms']:>8.1f}  {r['note']}")
    opened = sum(1 for r in results if r["open"])
    lines.append(f"{opened}/{len(results)} open")
    return "\n".join(lines)


def self_test():
    assert parse_ports("22,80,8000-8002,80") == [22, 80, 8000, 8001, 8002]
    for bad in ("", "0", "70000", "90-80", "x"):
        try:
            parse_ports(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted bad spec {bad!r}")
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    open_port = listener.getsockname()[1]
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    closed_port = probe.getsockname()[1]
    probe.close()
    try:
        assert check_port("127.0.0.1", open_port, 1.0)["open"] is True
        assert check_port("127.0.0.1", closed_port, 0.5)["open"] is False
    finally:
        listener.close()
    print("self-test OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("host", nargs="?")
    ap.add_argument("ports", nargs="?", help="comma list and/or ranges, e.g. 22,80,8000-8010")
    ap.add_argument("--timeout", type=float, default=2.0, help="seconds per connect (default 2)")
    ap.add_argument("--workers", type=int, default=32, help="concurrent probes (default 32)")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--self-test", action="store_true", help="run offline self tests")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.host or not args.ports:
        ap.error("host and ports are required")
    try:
        ports = parse_ports(args.ports)
    except ValueError as exc:
        ap.error(f"bad ports: {exc}")
    if args.timeout <= 0 or args.workers < 1:
        ap.error("--timeout and --workers must be positive")

    workers = min(args.workers, len(ports))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda p: check_port(args.host, p, args.timeout), ports))

    if args.json:
        print(json.dumps({"host": args.host, "results": results}, indent=2, sort_keys=True))
    else:
        print(render(args.host, results))
    return 0 if all(r["open"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
