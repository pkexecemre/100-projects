#!/usr/bin/env python3
"""Poll systemd units and log state changes with timestamps."""
import argparse
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_unit(unit):
    if shutil.which("systemctl") is None:
        return "unavailable"
    try:
        proc = subprocess.run(
            ["systemctl", "is-active", unit],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    lines = (proc.stdout or "").strip().splitlines()
    return lines[0] if lines else "unknown"


def read_units(units):
    return {unit: read_unit(unit) for unit in units}


def emit(line, out, logfile):
    out(line)
    if logfile:
        with open(logfile, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def watch(units, fetch, interval, ticks=None, out=print, logfile=None, sleep=time.sleep):
    previous = fetch(units)
    for unit in units:
        emit(f"[{now()}] {unit}: initial {previous.get(unit, 'unknown')}", out, logfile)
    changes = 0
    seen = 0
    while ticks is None or seen < ticks:
        sleep(interval)
        current = fetch(units)
        for unit in units:
            old = previous.get(unit, "unknown")
            new = current.get(unit, "unknown")
            if old != new:
                emit(f"[{now()}] {unit}: {old} -> {new}", out, logfile)
                changes += 1
        previous = current
        seen += 1
    return changes


def self_test():
    import tempfile

    sequence = iter([
        {"a.service": "active"},
        {"a.service": "active"},
        {"a.service": "failed"},
        {"a.service": "inactive"},
    ])
    lines = []
    with tempfile.TemporaryDirectory() as td:
        log = Path(td) / "watch.log"
        changes = watch(
            ["a.service"],
            lambda units: next(sequence),
            0,
            ticks=3,
            out=lines.append,
            logfile=str(log),
            sleep=lambda seconds: None,
        )
        assert changes == 2, changes
        text = log.read_text(encoding="utf-8")
        assert len(text.splitlines()) == len(lines)
    assert lines[0].endswith("initial active"), lines[0]
    assert any("active -> failed" in line for line in lines), lines
    assert "failed -> inactive" in lines[-1]
    print("self-test: ok")
    return 0


def main():
    if "--self-test" in sys.argv[1:]:
        return self_test()
    parser = argparse.ArgumentParser(description="Watch systemd units and log only state changes.")
    parser.add_argument("units", nargs="+", help="unit names, e.g. sshd.service")
    parser.add_argument("--interval", type=float, default=5.0, help="seconds between polls (default 5)")
    parser.add_argument("--once", action="store_true", help="print each unit's state once and exit")
    parser.add_argument("--log", metavar="FILE", help="also append change lines to FILE")
    args = parser.parse_args()
    if args.interval < 0:
        parser.error("--interval must be >= 0")
    if args.log:
        try:
            Path(args.log).parent.mkdir(parents=True, exist_ok=True)
            with open(args.log, "a", encoding="utf-8"):
                pass
        except OSError as exc:
            print(f"unit-watch: cannot open log file: {exc}", file=sys.stderr)
            return 2
    if args.once:
        for unit, state in read_units(args.units).items():
            emit(f"[{now()}] {unit}: {state}", print, args.log)
        return 0
    try:
        watch(args.units, read_units, args.interval, logfile=args.log)
    except KeyboardInterrupt:
        print("stopped", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
