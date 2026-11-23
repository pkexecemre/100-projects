#!/usr/bin/env python3
"""tls-expiry: inspect a TLS certificate's names and expiry date."""

import argparse
import json
import os
import socket
import ssl
import sys
import tempfile
import time


def cert_name(field, key="commonName"):
    for rdn in field or ():
        for name, value in rdn:
            if name == key:
                return value
    return ""


def describe_name(field):
    parts = []
    for key in ("commonName", "organizationName"):
        value = cert_name(field, key)
        if value:
            parts.append("%s=%s" % ("CN" if key == "commonName" else "O", value))
    return ", ".join(parts)


def days_left(not_after, now=None):
    if not not_after:
        return None
    try:
        expires = ssl.cert_time_to_seconds(not_after)
    except ValueError:
        return None
    current = time.time() if now is None else now
    return (expires - current) / 86400.0


def expiry_state(days, warn_days):
    if days is None:
        return "UNKNOWN"
    if days < 0:
        return "EXPIRED"
    if days <= warn_days:
        return "WARNING"
    return "OK"


def decode_der(der):
    """Decode a certificate when verification was disabled and cert is empty."""
    if not der:
        return {}
    path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False) as handle:
            handle.write(ssl.DER_cert_to_PEM_cert(der))
            path = handle.name
        decoder = getattr(getattr(ssl, "_ssl", None), "_test_decode_cert", None)
        return decoder(path) if decoder else {}
    except (OSError, ssl.SSLError, ValueError):
        return {}
    finally:
        if path:
            try:
                os.unlink(path)
            except OSError:
                pass


def fetch_cert(host, port, timeout, insecure, servername):
    context = ssl.create_default_context()
    if insecure:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    with socket.create_connection((host, port), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=servername) as tls:
            der = tls.getpeercert(binary_form=True)
            cert = tls.getpeercert() or decode_der(der)
            cipher = tls.cipher()
            return {
                "cert": cert,
                "tls_version": tls.version(),
                "cipher": cipher[0] if cipher else None,
                "verified": not insecure,
            }


def self_test():
    now = ssl.cert_time_to_seconds("Jun  1 12:00:00 2027 GMT")
    sample = "Jun  1 12:00:00 2027 GMT"
    assert abs(days_left(sample, now - 10 * 86400) - 10) < 1e-6
    assert abs(days_left(sample, now + 10 * 86400) + 10) < 1e-6
    assert days_left("garbage", now) is None and days_left(None, now) is None
    assert expiry_state(None, 30) == "UNKNOWN"
    assert expiry_state(-1, 30) == "EXPIRED"
    assert expiry_state(0, 30) == "WARNING"
    assert expiry_state(30, 30) == "WARNING"
    assert expiry_state(31, 30) == "OK"
    subject = ((("commonName", "example.test"),), (("organizationName", "Acme"),))
    assert cert_name(subject) == "example.test"
    assert describe_name(subject) == "CN=example.test, O=Acme"
    assert describe_name(()) == ""
    print("self-test: ok (expiry math, states, DN extraction)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check a TLS certificate's expiry.")
    ap.add_argument("host", nargs="?", help="hostname or IP")
    ap.add_argument("--port", type=int, default=443, help="TLS port (default: 443)")
    ap.add_argument("--servername", help="SNI name (default: HOST)")
    ap.add_argument("--timeout", type=float, default=10.0, help="seconds (default: 10)")
    ap.add_argument("--warn-days", type=float, default=30.0,
                    help="warn when this many days or fewer remain (default: 30)")
    ap.add_argument("-k", "--insecure", action="store_true",
                    help="do not verify the certificate chain")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--self-test", action="store_true", help="run offline checks")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.host:
        ap.error("HOST is required")
    host = args.host.strip()
    if not host or any(ch.isspace() for ch in host):
        print("error: invalid host %r" % args.host, file=sys.stderr)
        return 2
    if not 1 <= args.port <= 65535:
        ap.error("--port must be between 1 and 65535")
    if args.timeout <= 0:
        ap.error("--timeout must be greater than zero")
    if args.warn_days < 0:
        ap.error("--warn-days cannot be negative")

    try:
        info = fetch_cert(host, args.port, args.timeout, args.insecure,
                          args.servername or host)
    except ssl.SSLCertVerificationError as exc:
        print("error: certificate verification failed: %s" % exc.verify_message,
              file=sys.stderr)
        print("hint: retry with --insecure to inspect an untrusted certificate",
              file=sys.stderr)
        return 2
    except (OSError, ssl.SSLError, ValueError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2

    cert = info["cert"]
    subject = describe_name(cert.get("subject"))
    issuer = describe_name(cert.get("issuer"))
    not_after = cert.get("notAfter")
    days = days_left(not_after)
    state = expiry_state(days, args.warn_days)
    sans = [value for kind, value in cert.get("subjectAltName", ()) if kind == "DNS"]
    result = {
        "host": host,
        "port": args.port,
        "subject": subject,
        "issuer": issuer,
        "not_before": cert.get("notBefore"),
        "not_after": not_after,
        "days_left": None if days is None else round(days, 2),
        "state": state,
        "warn_days": args.warn_days,
        "tls_version": info["tls_version"],
        "cipher": info["cipher"],
        "verified": info["verified"],
        "dns_sans": sans,
    }
    if args.json:
        print(json.dumps(result))
    else:
        print("host: %s:%d" % (host, args.port))
        print("subject: %s" % (subject or "-"))
        print("issuer: %s" % (issuer or "-"))
        print("not_before: %s" % (cert.get("notBefore") or "-"))
        print("not_after: %s" % (not_after or "-"))
        print("days_left: %s" % ("-" if days is None else "%.1f" % days))
        print("status: %s (warn at %g days)" % (state, args.warn_days))
        print("tls: %s / %s" % (info["tls_version"], info["cipher"] or "-"))
        if sans:
            print("dns_sans: %s" % ", ".join(sans))
    if state == "UNKNOWN":
        print("error: certificate expiry could not be decoded", file=sys.stderr)
        return 2
    return 1 if state in ("WARNING", "EXPIRED") else 0


if __name__ == "__main__":
    sys.exit(main())
