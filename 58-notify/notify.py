#!/usr/bin/env python3
"""Send a desktop notification with notify-send, falling back to the terminal."""
import argparse
import io
import os
import shutil
import subprocess
import sys

URGENCIES = ("low", "normal", "critical")


def notification_args(title, body, urgency, app, expire):
    args = ["notify-send", "-u", urgency, "-a", app, "-t", str(expire), title]
    if body:
        args.append(body)
    return args


def fallback_text(title, body, urgency):
    text = f"[{urgency.upper()}] {title}"
    if body:
        text += f": {body}"
    return text


def can_notify():
    has_tool = shutil.which("notify-send") is not None
    has_display = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return has_tool and has_display


def validate(title, urgency, expire):
    if not title.strip():
        raise ValueError("title is empty")
    if urgency not in URGENCIES:
        raise ValueError(f"urgency must be one of {', '.join(URGENCIES)}")
    if expire < 0:
        raise ValueError("--expire must be >= 0")


def notify(title, body="", urgency="normal", app="notify", expire=5000,
           force_terminal=False, stream=sys.stderr, runner=subprocess.run):
    validate(title, urgency, expire)
    if not force_terminal and can_notify():
        try:
            proc = runner(
                notification_args(title, body, urgency, app, expire),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode == 0:
                return "notify-send", proc
            stream.write(f"notify: notify-send exited {proc.returncode}; using terminal fallback\n")
        except (OSError, subprocess.SubprocessError) as exc:
            stream.write(f"notify: notify-send failed ({exc}); using terminal fallback\n")
    stream.write(fallback_text(title, body, urgency) + "\n")
    stream.flush()
    return "terminal", None


def self_test():
    assert validate("Title", "low", 0) is None
    try:
        validate("Title", "high", 1000)
        raise AssertionError("bad urgency must fail")
    except ValueError:
        pass
    try:
        validate("   ", "normal", 1000)
        raise AssertionError("blank title must fail")
    except ValueError:
        pass
    args = notification_args("Title", "Body", "critical", "backup", 1500)
    assert args[0] == "notify-send"
    assert args[args.index("-u") + 1] == "critical"
    assert args[args.index("-a") + 1] == "backup"
    assert args[args.index("-t") + 1] == "1500"
    assert args[-1] == "Body"
    assert notification_args("Title", "", "low", "app", 0)[-1] == "Title"
    buffer = io.StringIO()
    method, _ = notify("Disk full", "root at 98%", "critical", force_terminal=True, stream=buffer)
    assert method == "terminal"
    assert buffer.getvalue().strip() == "[CRITICAL] Disk full: root at 98%", buffer.getvalue()
    print("self-test: ok")
    return 0


def main():
    if "--self-test" in sys.argv[1:]:
        return self_test()
    parser = argparse.ArgumentParser(description="Desktop notification with a terminal fallback.")
    parser.add_argument("title", help="notification summary")
    parser.add_argument("body", nargs="?", default="", help="optional body text")
    parser.add_argument("-u", "--urgency", default="normal", choices=URGENCIES, help="urgency level")
    parser.add_argument("-a", "--app", default="notify", help="application name shown by the daemon")
    parser.add_argument("-t", "--expire", type=int, default=5000, metavar="MS", help="expiry in milliseconds")
    parser.add_argument("--force-terminal", action="store_true", help="skip notify-send and print to stderr")
    args = parser.parse_args()
    try:
        notify(
            args.title, args.body, args.urgency, args.app, args.expire,
            force_terminal=args.force_terminal,
        )
    except (ValueError, OSError) as exc:
        print(f"notify: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
