#!/usr/bin/env python3
"""Check HTTP(S) URLs: status, redirect chain length and total latency."""

import argparse
import http.client
import json
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


class CountingRedirects(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        self.count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.count += 1
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def reason_text(reason):
    if isinstance(reason, socket.gaierror):
        return f"dns: {reason.strerror or reason}"
    return getattr(reason, "strerror", None) or str(reason)


def check_url(url, timeout):
    parsed_url = urllib.parse.urlparse(url)
    if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
        return {"url": url, "status": None, "ok": False, "redirects": 0, "ms": 0.0,
                "final_url": url, "note": "only absolute http/https URLs are supported"}

    handler = CountingRedirects()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), handler)
    request = urllib.request.Request(url, headers={"User-Agent": "url-check/1.0"})
    started = time.perf_counter()
    status, note, final_url = None, "", url
    try:
        with opener.open(request, timeout=timeout) as response:
            status = response.status
            final_url = response.geturl()
            response.read(1024)
        note = "ok" if 200 <= status < 400 else f"HTTP {status}"
    except urllib.error.HTTPError as exc:
        status = exc.code
        final_url = exc.geturl() or url
        note = f"HTTP {status} {exc.reason}".strip()
        exc.close()
    except urllib.error.URLError as exc:
        note = reason_text(exc.reason)
    except (TimeoutError, socket.timeout):
        note = f"timeout after {timeout:g}s"
    except (http.client.HTTPException, ValueError, OSError) as exc:
        note = str(exc) or exc.__class__.__name__
    elapsed = round((time.perf_counter() - started) * 1000, 1)
    ok = status is not None and 200 <= status < 400
    return {"url": url, "status": status, "ok": ok, "redirects": handler.count,
            "ms": elapsed, "final_url": final_url, "note": note or "ok"}


def fit(text, width):
    return text if len(text) <= width else text[: width - 3] + "..."


def render(results):
    lines = [f"{'URL':48} {'STATUS':6} {'REDIR':5} {'MS':>8}  NOTE"]
    for r in results:
        status = str(r["status"]) if r["status"] is not None else "ERR"
        lines.append(f"{fit(r['url'], 48):48} {status:6} {r['redirects']:>5} "
                     f"{r['ms']:>8.1f}  {r['note']}")
    good = sum(1 for r in results if r["ok"])
    lines.append(f"{good}/{len(results)} ok")
    return "\n".join(lines)


def self_test():
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/ok":
                body, code, location = b"ok", 200, None
            elif self.path == "/redirect":
                body, code, location = b"", 302, "/ok"
            else:
                body, code, location = b"missing", 404, None
            self.send_response(code)
            if location:
                self.send_header("Location", location)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        direct = check_url(base + "/ok", 2)
        assert direct["ok"] and direct["status"] == 200 and direct["redirects"] == 0, direct
        moved = check_url(base + "/redirect", 2)
        assert moved["ok"] and moved["status"] == 200 and moved["redirects"] == 1, moved
        missing = check_url(base + "/missing", 2)
        assert not missing["ok"] and missing["status"] == 404, missing

        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.bind(("127.0.0.1", 0))
        dead_port = probe.getsockname()[1]
        probe.close()
        dead = check_url(f"http://127.0.0.1:{dead_port}/", 0.5)
        assert not dead["ok"] and dead["status"] is None and dead["note"], dead
        assert not check_url("file:///etc/passwd", 1)["ok"]
        assert "REDIR" in render([direct, moved])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    print("self-test OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("urls", nargs="*", help="absolute http:// or https:// URLs")
    ap.add_argument("--timeout", type=float, default=10.0, help="seconds per request (default 10)")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--self-test", action="store_true", help="run offline self tests")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.urls:
        ap.error("at least one URL is required")
    if args.timeout <= 0:
        ap.error("--timeout must be positive")

    results = [check_url(url, args.timeout) for url in args.urls]
    if args.json:
        print(json.dumps({"results": results}, indent=2, sort_keys=True))
    else:
        print(render(results))
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
