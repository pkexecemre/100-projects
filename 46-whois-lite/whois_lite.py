#!/usr/bin/env python3
"""whois-lite: raw WHOIS query over TCP with optional referral following."""

import argparse
import json
import re
import socket
import sys

HOST_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?$")
QUERY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.:-]*$")
REFERRAL_RE = re.compile(r"^\s*(?:refer|whois|referralserver)\s*:\s*(\S+)\s*$", re.I)
MAX_RESPONSE = 2_000_000


def validate_query(query):
    value = query.strip()
    if not value:
        raise ValueError("empty query")
    if len(value) > 253:
        raise ValueError("query is too long")
    if not QUERY_RE.match(value) or ".." in value:
        raise ValueError("query contains unsupported characters")
    return value


def validate_server(server):
    value = server.strip().lower().rstrip(".")
    if not HOST_RE.match(value):
        raise ValueError("invalid whois server %r" % server)
    return value


def parse_fields(text):
    fields = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped[0] in "%#":
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key, value = key.strip().lower(), value.strip()
        if key and value:
            fields.setdefault(key, []).append(value)
    return fields


def find_referral(text):
    for line in text.splitlines():
        match = REFERRAL_RE.match(line)
        if not match:
            continue
        host = match.group(1).lower().rstrip(".")
        if HOST_RE.match(host):
            return host
    return None


def query_whois(server, port, query, timeout):
    if not 1 <= port <= 65535:
        raise ValueError("port out of range")
    with socket.create_connection((server, port), timeout=timeout) as sock:
        sock.sendall((query + "\r\n").encode("ascii"))
        chunks = []
        total = 0
        while True:
            data = sock.recv(65536)
            if not data:
                break
            chunks.append(data)
            total += len(data)
            if total > MAX_RESPONSE:
                raise RuntimeError("response exceeded %d bytes" % MAX_RESPONSE)
    return b"".join(chunks).decode("utf-8", "replace")


def self_test():
    sample = "\n".join([
        "% IANA WHOIS server",
        "% for more information on IANA, visit http://www.iana.org",
        "domain:       EXAMPLE",
        "organisation: Example Org",
        "refer:        whois.example.net",
        "",
        "created:      1995-08-14",
        "created:      2024-01-01",
        "status:       ACTIVE",
    ])
    fields = parse_fields(sample)
    assert fields["domain"] == ["EXAMPLE"]
    assert fields["created"] == ["1995-08-14", "2024-01-01"]
    assert "IANA WHOIS" not in "".join(fields)
    assert find_referral(sample) == "whois.example.net"
    assert find_referral("domain: x\nrefer: not a host!") is None
    assert validate_query("example.com") == "example.com"
    assert validate_query("2001:db8::1") == "2001:db8::1"
    for bad in ("", "has space", "bad\nquery", "-flag", "a..b", "x" * 300):
        try:
            validate_query(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("accepted bad query %r" % bad)
    assert validate_server("whois.iana.org") == "whois.iana.org"
    try:
        validate_server("bad host")
    except ValueError:
        pass
    else:
        raise AssertionError("accepted bad server")
    print("self-test: ok (query validation, field parsing, referral detection)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Minimal WHOIS client.")
    ap.add_argument("query", nargs="?", help="domain name or IP address")
    ap.add_argument("--server", default="whois.iana.org",
                    help="whois server (default: whois.iana.org)")
    ap.add_argument("--port", type=int, default=43, help="TCP port (default: 43)")
    ap.add_argument("--timeout", type=float, default=10.0, help="seconds (default: 10)")
    ap.add_argument("--follow", action="store_true",
                    help="follow one refer:/whois: referral")
    ap.add_argument("--json", action="store_true", help="parsed key/value output")
    ap.add_argument("--self-test", action="store_true", help="run offline checks")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.query:
        ap.error("QUERY is required")
    if args.timeout <= 0:
        ap.error("--timeout must be greater than zero")
    try:
        query = validate_query(args.query)
        server = validate_server(args.server)
        if not 1 <= args.port <= 65535:
            raise ValueError("--port must be between 1 and 65535")
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2

    try:
        raw = query_whois(server, args.port, query, args.timeout)
        referral = None
        if args.follow:
            referral = find_referral(raw)
            if referral and referral != server:
                print("following referral: %s" % referral, file=sys.stderr)
                raw = query_whois(referral, 43, query, args.timeout)
                server = referral
    except (OSError, RuntimeError, ValueError) as exc:
        print("error: whois query failed: %s" % exc, file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"query": query, "server": server,
                          "fields": parse_fields(raw), "raw": raw}))
    else:
        sys.stdout.write(raw if raw.endswith("\n") else raw + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
