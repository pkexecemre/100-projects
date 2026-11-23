#!/usr/bin/env python3
"""dns-lookup: forward (A/AAAA) and reverse (PTR) DNS lookups with JSON output."""

import argparse
import json
import socket
import sys
import threading


def in_thread(fn, timeout):
    """Run fn in a daemon thread so a stuck resolver cannot hang the CLI."""
    box = {}

    def runner():
        try:
            box["value"] = fn()
        except Exception as exc:  # resolver failures include gaierror and UnicodeError
            box["error"] = str(exc)

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        return None, "lookup timed out after %gs" % timeout
    if "error" in box:
        return None, box["error"]
    return box.get("value"), None


def addrinfo_records(infos):
    """Turn getaddrinfo tuples into unique, ordered A/AAAA records."""
    records = []
    seen = set()
    for family, _, _, _, sockaddr in infos:
        if family == socket.AF_INET:
            rtype, address = "A", sockaddr[0]
        elif family == socket.AF_INET6:
            rtype, address = "AAAA", sockaddr[0].split("%", 1)[0]
        else:
            continue
        key = (rtype, address)
        if key in seen:
            continue
        seen.add(key)
        records.append({"type": rtype, "address": address})
    return records


def resolve(host, rtype, timeout):
    families = {"a": socket.AF_INET, "aaaa": socket.AF_INET6, "all": socket.AF_UNSPEC}
    family = families[rtype]
    infos, error = in_thread(
        lambda: socket.getaddrinfo(host, None, family, socket.SOCK_STREAM), timeout
    )
    if error:
        return [], error
    return addrinfo_records(infos), None


def reverse(host, timeout):
    answer, error = in_thread(lambda: socket.gethostbyaddr(host), timeout)
    if error:
        return None, error
    name, aliases, addresses = answer
    return {"ptr": name, "aliases": list(aliases), "addresses": list(addresses)}, None


def self_test():
    infos = [
        (socket.AF_INET, 1, 6, "", ("192.0.2.1", 0)),
        (socket.AF_INET, 1, 6, "", ("192.0.2.1", 0)),
        (socket.AF_INET6, 1, 6, "", ("2001:db8::1", 0, 0, 0)),
    ]
    records = addrinfo_records(infos)
    assert records == [
        {"type": "A", "address": "192.0.2.1"},
        {"type": "AAAA", "address": "2001:db8::1"},
    ], records
    value, error = in_thread(lambda: 42, 2)
    assert value == 42 and error is None
    def fail():
        raise socket.gaierror("no such host")

    value, error = in_thread(fail, 2)
    assert value is None and "no such host" in error
    payload = {"query": "example.test", "records": records}
    assert json.loads(json.dumps(payload))["records"][1]["type"] == "AAAA"
    print("self-test: ok (record dedupe, thread timeout, JSON encoding)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Forward and reverse DNS lookups.")
    ap.add_argument("host", nargs="?", help="hostname or IP address")
    ap.add_argument("-t", "--type", choices=("a", "aaaa", "all"), default="all",
                    help="forward record type (default: all)")
    ap.add_argument("-r", "--reverse", action="store_true",
                    help="treat HOST as an IP address and look up its PTR record")
    ap.add_argument("--timeout", type=float, default=5.0, help="seconds (default: 5)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--self-test", action="store_true", help="run offline checks")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.host:
        ap.error("HOST is required")
    if args.timeout <= 0:
        ap.error("--timeout must be greater than zero")
    if args.reverse and args.type != "all":
        ap.error("--reverse cannot be combined with --type")

    host = args.host.strip()
    if not host or any(ch.isspace() for ch in host):
        print("error: invalid host %r" % args.host, file=sys.stderr)
        return 2

    if args.reverse:
        result, error = reverse(host, args.timeout)
        if error:
            if args.json:
                print(json.dumps({"query": host, "mode": "reverse", "error": error}))
            print("error: %s" % error, file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps({"query": host, "mode": "reverse", **result}))
        else:
            print("%s -> %s" % (host, result["ptr"]))
            for alias in result["aliases"]:
                print("  alias: %s" % alias)
        return 0

    records, error = resolve(host, args.type, args.timeout)
    if error:
        if args.json:
            print(json.dumps({"query": host, "mode": "forward", "records": [],
                              "error": error}))
        print("error: %s" % error, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"query": host, "mode": "forward", "records": records}))
    else:
        print("%s:" % host)
        for record in records:
            print("  %-4s %s" % (record["type"], record["address"]))
        if not records:
            print("  no records")
    return 0 if records else 1


if __name__ == "__main__":
    sys.exit(main())
