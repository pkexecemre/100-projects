#!/usr/bin/env python3
"""download-speed: stream a URL to /dev/null and report average throughput."""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

CHUNK = 65536


def format_bytes(count):
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    value = float(count)
    index = 0
    while value >= 1024 and index < len(units) - 1:
        value /= 1024
        index += 1
    if index == 0:
        return "%d B" % int(value)
    return "%.1f %s" % (value, units[index])


def format_rate(bytes_per_second):
    if bytes_per_second <= 0:
        return "0 B/s"
    if bytes_per_second >= 1_000_000:
        return "%.2f MB/s" % (bytes_per_second / 1_000_000)
    if bytes_per_second >= 1_000:
        return "%.1f kB/s" % (bytes_per_second / 1_000)
    return "%.0f B/s" % bytes_per_second


def measure(read, write, clock=time.monotonic, content_length=None, on_progress=None):
    """Copy read() -> write() and return (bytes, seconds)."""
    started = clock()
    total = 0
    while True:
        chunk = read(CHUNK)
        if not chunk:
            break
        write(chunk)
        total += len(chunk)
        if on_progress:
            elapsed = max(clock() - started, 1e-9)
            on_progress(total, content_length, elapsed)
    return total, max(clock() - started, 1e-9)


class Progress:
    def __init__(self, enabled=True, interval=0.2):
        self.enabled = enabled
        self.interval = interval
        self.last = -interval
        self.printed = False

    def __call__(self, total, length, elapsed):
        if not self.enabled or elapsed - self.last < self.interval:
            return
        self.last = elapsed
        self.printed = True
        message = "\r%s" % format_bytes(total)
        if length:
            message += " / %s (%5.1f%%)" % (format_bytes(length), 100.0 * total / length)
        message += "  %s" % format_rate(total / elapsed)
        print(message, end="", file=sys.stderr, flush=True)

    def done(self):
        if self.printed:
            print(file=sys.stderr, flush=True)


def self_test():
    assert format_bytes(0) == "0 B"
    assert format_bytes(1536) == "1.5 KiB"
    assert format_bytes(1024 ** 2) == "1.0 MiB"
    assert format_rate(0) == "0 B/s"
    assert format_rate(999) == "999 B/s"
    assert format_rate(1500) == "1.5 kB/s"
    assert format_rate(2_500_000) == "2.50 MB/s"
    ticks = iter([0.0, 0.5, 1.0])
    total, elapsed = measure(lambda n: b"", lambda chunk: None, clock=lambda: next(ticks))
    assert total == 0 and elapsed == 0.5, (total, elapsed)
    stream = __import__("io").BytesIO(b"x" * 10)
    ticks = iter([0.0, 0.6, 1.0])
    total, elapsed = measure(stream.read, lambda chunk: None, clock=lambda: next(ticks),
                             on_progress=lambda *args: None)
    assert total == 10 and elapsed == 1.0, (total, elapsed)
    print("self-test: ok (byte/rate formatting, meter loop)")
    return 0


def download(url, timeout, quiet):
    if not url.startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")
    request = urllib.request.Request(url, headers={"User-Agent": "download-speed/1.0"})
    started = time.monotonic()
    progress = Progress(not quiet)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        length_text = response.headers.get("Content-Length")
        length = int(length_text) if length_text and length_text.isdigit() else None
        with open(os.devnull, "wb") as sink:
            total, _ = measure(response.read, sink.write, content_length=length,
                               on_progress=progress)
        progress.done()
        elapsed = max(time.monotonic() - started, 1e-9)
        return {
            "url": response.geturl(),
            "bytes": total,
            "seconds": round(elapsed, 3),
            "mb_per_second": round(total / elapsed / 1_000_000, 3),
            "status": response.status,
            "content_type": response.headers.get("Content-Type"),
            "content_length": length,
        }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Measure download throughput.")
    ap.add_argument("url", nargs="?", help="http(s) URL to download")
    ap.add_argument("--timeout", type=float, default=30.0,
                    help="socket timeout in seconds (default: 30)")
    ap.add_argument("-q", "--quiet", action="store_true", help="no progress on stderr")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--self-test", action="store_true", help="run offline checks")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.url:
        ap.error("URL is required")
    if args.timeout <= 0:
        ap.error("--timeout must be greater than zero")

    try:
        result = download(args.url.strip(), args.timeout, args.quiet)
    except urllib.error.HTTPError as exc:
        print("error: HTTP %d %s" % (exc.code, exc.reason), file=sys.stderr)
        return 2
    except (urllib.error.URLError, ValueError, OSError) as exc:
        print("error: %s" % getattr(exc, "reason", exc), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130

    if args.json:
        print(json.dumps(result))
    else:
        print("Downloaded %s in %.2fs (%s)" % (
            format_bytes(result["bytes"]),
            result["seconds"],
            format_rate(result["bytes"] / max(result["seconds"], 1e-9)),
        ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
