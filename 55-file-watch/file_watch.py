#!/usr/bin/env python3
"""Poll a file or directory for changes and run a command when something changes."""
import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def snapshot(path):
    target = Path(path)
    state = {}
    if target.is_file():
        stat = target.stat()
        state[str(target)] = (stat.st_mtime_ns, stat.st_size)
        return state
    if not target.is_dir():
        raise FileNotFoundError(f"no such file or directory: {target}")
    for root, dirs, names in os.walk(target):
        dirs[:] = sorted(d for d in dirs if d not in (".git", "__pycache__"))
        for name in names:
            entry = Path(root) / name
            try:
                stat = entry.stat()
            except OSError:
                continue
            state[str(entry)] = (stat.st_mtime_ns, stat.st_size)
    return state


def diff(previous, current):
    return {
        "added": sorted(set(current) - set(previous)),
        "changed": sorted(key for key in set(previous) & set(current) if previous[key] != current[key]),
        "removed": sorted(set(previous) - set(current)),
    }


def describe(delta):
    parts = [f"{len(delta[name])} {name}" for name in ("added", "changed", "removed") if delta[name]]
    return ", ".join(parts) if parts else "no change"


def split_argv(argv):
    if "--" in argv:
        index = argv.index("--")
        return argv[:index], argv[index + 1:]
    return argv, []


def run_command(command, use_exec=False):
    if use_exec:
        return subprocess.run(command).returncode
    return subprocess.run(" ".join(command), shell=True).returncode


def watch(path, command, interval=1.0, once=False, use_exec=False, ticks=None,
          fetch=snapshot, run=None, out=print, sleep=time.sleep):
    runner = run or (lambda cmd: run_command(cmd, use_exec))
    previous = fetch(path)
    seen = 0
    while ticks is None or seen < ticks:
        sleep(interval)
        current = fetch(path)
        delta = diff(previous, current)
        if any(delta.values()):
            out(f"[{now()}] change detected: {describe(delta)}")
            for label in ("added", "changed", "removed"):
                for item in delta[label][:5]:
                    out(f"  {label}: {item}")
                if len(delta[label]) > 5:
                    out(f"  ... and {len(delta[label]) - 5} more {label}")
            code = runner(command)
            out(f"[{now()}] command exited {code}")
            if once:
                return code
        previous = current
        seen += 1
    return 0


def self_test():
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        note = root / "note.txt"
        note.write_text("a", encoding="utf-8")
        base = snapshot(root)
        stat = note.stat()
        modified = dict(base)
        modified[str(note)] = (stat.st_mtime_ns + 1, stat.st_size + 1)
        sequence = iter([base, modified, modified])
        calls = []

        def fake_run(command):
            calls.append(command)
            return 7

        code = watch(
            root,
            ["echo", "hi"],
            interval=0,
            once=True,
            ticks=3,
            fetch=lambda path: next(sequence),
            run=fake_run,
            out=lambda line: None,
            sleep=lambda seconds: None,
        )
        assert code == 7, code
        assert calls == [["echo", "hi"]], calls
        delta = diff(base, dict(modified, **{str(root / "new.txt"): (1, 1)}))
        assert delta["changed"] == [str(note)] and delta["added"], delta
        assert describe(delta) == "1 added, 1 changed", describe(delta)
        try:
            snapshot(root / "missing")
            raise AssertionError("missing path must fail")
        except FileNotFoundError:
            pass
    print("self-test: ok")
    return 0


def main():
    if "--self-test" in sys.argv[1:]:
        return self_test()
    raw, words = split_argv(sys.argv[1:])
    parser = argparse.ArgumentParser(description="Watch a path and run a command whenever its contents change.")
    parser.add_argument("path", help="file or directory to watch")
    parser.add_argument("--interval", type=float, default=1.0, help="seconds between scans (default 1)")
    parser.add_argument("--once", action="store_true", help="run on the first change, then exit")
    parser.add_argument("--exec", dest="use_exec", action="store_true",
                        help="execute argv directly instead of through /bin/sh")
    args = parser.parse_args(raw)
    if not words:
        parser.error("no command given (usage: file_watch.py PATH [options] -- CMD...)")
    if args.interval < 0:
        parser.error("--interval must be >= 0")
    try:
        code = watch(args.path, words, args.interval, args.once, args.use_exec)
    except FileNotFoundError as exc:
        print(f"file-watch: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("stopped", file=sys.stderr)
        return 0
    return code if args.once else 0


if __name__ == "__main__":
    sys.exit(main())
