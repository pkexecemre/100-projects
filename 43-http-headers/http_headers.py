#!/usr/bin/env python3
"""http-headers: fetch a URL and dump status, redirect chain, and headers."""

import argparse
import json
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request


def normalize_url(raw):
    raw = raw.strip()
    if not raw:
        raise ValueError("empty URL")
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urllib.parse.urlsplit(raw)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("URL must be absolute http:// or https://")
    return raw


def sorted_headers(headers):
    return sorted(headers, key=lambda item: item[0].lower())


def render(status, reason, url, headers, chain):
    lines = ["URL: %s" % url, ("Status: %s %s" % (status, reason)).rstrip()]
    if chain:
        lines.append("Redirects:")
        for hop in chain:
            lines.append("  %d %s -> %s" % (hop["status"], hop["url"], hop["location"]))
    lines.append("Headers:")
    for name, value in sorted_headers(headers):
        lines.append("  %s: %s" % (name, value))
    return "\n".join(lines)


def make_opener(chain, max_redirects, insecure):
    class Recorder(urllib.request.HTTPRedirectHandler):
        def __init__(self):
            super().__init__()
            self.max_redirections = max_redirects

        def redirect_request(self, req, fp, code, msg, headers, newurl):
            chain.append({"status": code, "url": req.full_url, "location": newurl})
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    handlers = [Recorder()]
    if insecure:
        handlers.append(urllib.request.HTTPSHandler(context=ssl._create_unverified_context()))
    return urllib.request.build_opener(*handlers)


def fetch(url, method, timeout, insecure, max_redirects):
    chain = []
    opener = make_opener(chain, max_redirects, insecure)
    req = urllib.request.Request(url, method=method,
                                 headers={"User-Agent": "http-headers/1.0"})
    try:
        resp = opener.open(req, timeout=timeout)
    except urllib.error.HTTPError as exc:
        if method == "HEAD" and exc.code in (405, 501):
            req = urllib.request.Request(url, method="GET",
                                         headers={"User-Agent": "http-headers/1.0"})
            resp = opener.open(req, timeout=timeout)
        else:
            raise
    with resp:
        return {
            "url": resp.geturl(),
            "status": resp.status,
            "reason": resp.reason,
            "redirects": chain,
            "headers": sorted_headers(list(resp.headers.items())),
        }


def emit(result, as_json):
    if as_json:
        print(json.dumps(result))
    else:
        print(render(result["status"], result["reason"], result["url"],
                     result["headers"], result["redirects"]))


def self_test():
    assert normalize_url("example.test") == "https://example.test"
    assert normalize_url("http://example.test/a?b=1").startswith("http://")
    for bad in ("", "ftp://example.test", "https://", "://x"):
        try:
            normalize_url(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("accepted bad URL %r" % bad)
    headers = [("B", "2"), ("a", "1"), ("b", "3")]
    assert sorted_headers(headers) == [("a", "1"), ("B", "2"), ("b", "3")]
    text = render(301, "Moved", "http://x/", headers,
                  [{"status": 301, "url": "http://x/", "location": "http://y/"}])
    assert "Status: 301 Moved" in text and "-> http://y/" in text
    assert "  a: 1" in text and "  B: 2" in text
    print("self-test: ok (URL validation, header sorting, rendering)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Dump HTTP response headers.")
    ap.add_argument("url", nargs="?", help="http(s) URL; https:// is assumed")
    ap.add_argument("-X", "--method", choices=("HEAD", "GET"), default="HEAD",
                    help="request method (default: HEAD, falls back to GET on 405/501)")
    ap.add_argument("--timeout", type=float, default=10.0, help="seconds (default: 10)")
    ap.add_argument("--max-redirects", type=int, default=10, help="redirect limit")
    ap.add_argument("-k", "--insecure", action="store_true", help="skip TLS verification")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--self-test", action="store_true", help="run offline checks")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.url:
        ap.error("URL is required")
    if args.timeout <= 0:
        ap.error("--timeout must be greater than zero")
    if args.max_redirects < 0:
        ap.error("--max-redirects cannot be negative")
    try:
        url = normalize_url(args.url)
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2

    try:
        result = fetch(url, args.method, args.timeout, args.insecure, args.max_redirects)
    except urllib.error.HTTPError as exc:
        headers = sorted_headers(list(exc.headers.items())) if exc.headers else []
        result = {"url": exc.geturl(), "status": exc.code, "reason": exc.reason,
                  "redirects": [], "headers": headers}
        emit(result, args.json)
        print("error: HTTP %d %s" % (exc.code, exc.reason), file=sys.stderr)
        return 1
    except (urllib.error.URLError, ssl.SSLError, TimeoutError, ValueError) as exc:
        reason = getattr(exc, "reason", exc)
        print("error: %s" % reason, file=sys.stderr)
        return 2
    emit(result, args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
