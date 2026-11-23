#!/usr/bin/env python3
"""Countdown timer with a desktop notification and terminal fallback."""

import argparse
import io
import shutil
import subprocess
import sys
import time

MAX_SECONDS = 24 * 3600


def format_duration(total):
    total = max(0, int(total))
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def notify_send(title, message):
    """Send a desktop notification. Returns False when unavailable."""
    if not shutil.which("notify-send"):
        return False
    try:
        result = subprocess.run(
            ["notify-send", "--urgency=normal", title, message],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def run_timer(seconds, label, quiet=False, use_notify=True, out=None,
              sleep=time.sleep, clock=time.monotonic):
    """Run the countdown, update once per half second, return notification state."""
    out = sys.stdout if out is None else out
    interactive = bool(getattr(out, "isatty", lambda: False)())
    end = clock() + seconds
    while True:
        remaining = end - clock()
        if remaining <= 0:
            break
        if not quiet and interactive:
            out.write("\r" + format_duration(remaining) + " remaining ")
            out.flush()
        sleep(min(0.5, remaining))
    if not quiet:
        if interactive:
            out.write("\r" + format_duration(0) + " remaining \n")
        out.write(f"Done: {label}\n")
        out.flush()
    return bool(use_notify and notify_send("Countdown finished", label))


def self_test():
    assert format_duration(0) == "00:00"
    assert format_duration(59) == "00:59"
    assert format_duration(60) == "01:00"
    assert format_duration(3661) == "01:01:01"
    buffer = io.StringIO()
    started = time.monotonic()
    notified = run_timer(0, "self-test", out=buffer, use_notify=False)
    assert not notified
    assert time.monotonic() - started < 2
    assert "Done: self-test" in buffer.getvalue()
    assert "remaining" not in buffer.getvalue()
    quiet_buffer = io.StringIO()
    run_timer(0, "quiet", quiet=True, use_notify=False, out=quiet_buffer)
    assert quiet_buffer.getvalue() == ""
    print("self-test OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Countdown timer that prints progress and notifies when done.",
        epilog="Uses notify-send when installed and falls back to a terminal "
        "bell. Exit codes: 0 success, 2 usage error.",
    )
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--seconds", type=int, metavar="N", help="duration in seconds")
    group.add_argument("--minutes", type=int, metavar="N", help="duration in minutes")
    ap.add_argument("--label", default="Timer", help="text shown when time is up")
    ap.add_argument("--quiet", action="store_true", help="no progress or done output")
    ap.add_argument("--no-notify", action="store_true", help="skip notify-send")
    ap.add_argument("--self-test", action="store_true", help="run built-in checks")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.seconds is None and args.minutes is None:
        ap.error("one of --seconds or --minutes is required")
    seconds = args.seconds if args.seconds is not None else args.minutes * 60
    if seconds < 0:
        ap.error("duration must not be negative")
    if seconds > MAX_SECONDS:
        ap.error(f"duration must be at most {MAX_SECONDS} seconds")

    notified = run_timer(seconds, args.label, args.quiet, not args.no_notify)
    if not args.quiet and not notified and sys.stdout.isatty():
        sys.stdout.write("\a")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
