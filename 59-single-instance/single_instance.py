#!/usr/bin/env python3
"""Run a command under an exclusive flock so duplicate instances exit quickly."""
import argparse
import fcntl
import hashlib
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

EX_TEMPFAIL = 75


def default_lock(command):
    key = hashlib.sha256(f"{os.getuid()}:{' '.join(command)}".encode("utf-8")).hexdigest()[:12]
    base = os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir()
    return str(Path(base) / f"single-instance-{key}.lock")


def read_pid(path):
    try:
        text = Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return int(text) if text.isdigit() else None


def pid_alive(pid):
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def lock_age(path):
    try:
        return max(0.0, time.time() - Path(path).stat().st_mtime)
    except OSError:
        return 0.0


def acquire(path, timeout=0.0, stale=0.0):
    """Return (handle, prior pid, reclaimed pid), or (None, holder, None) on timeout."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + max(0.0, timeout)
    while True:
        handle = open(path, "a+", encoding="utf-8")
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            holder = read_pid(path)
            handle.close()
            if time.monotonic() >= deadline:
                return None, holder, None
            time.sleep(min(0.25, max(0.02, timeout / 10)))
            continue
        previous = read_pid(path)
        reclaimed = None
        if previous and previous != os.getpid() and not pid_alive(previous) and lock_age(path) >= stale:
            reclaimed = previous
        handle.seek(0)
        handle.truncate()
        handle.write(str(os.getpid()) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
        return handle, previous, reclaimed


def split_argv(argv):
    if "--" in argv:
        index = argv.index("--")
        return argv[:index], argv[index + 1:]
    return argv, []


def release(handle):
    try:
        fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        handle.close()


def self_test():
    script = os.path.abspath(__file__)
    with tempfile.TemporaryDirectory() as td:
        lock = str(Path(td) / "job.lock")
        handle, holder, reclaimed = acquire(lock)
        assert handle is not None and holder is None and reclaimed is None
        child = subprocess.run(
            [sys.executable, script, "--lock", lock, "--timeout", "0", "--",
             sys.executable, "-c", "print('should-not-run')"],
            capture_output=True, text=True,
        )
        assert child.returncode == EX_TEMPFAIL, (child.returncode, child.stdout, child.stderr)
        assert "should-not-run" not in child.stdout
        release(handle)
        child = subprocess.run(
            [sys.executable, script, "--lock", lock, "--timeout", "0", "--",
             sys.executable, "-c", "print('ran-once')"],
            capture_output=True, text=True,
        )
        assert child.returncode == 0, child.stderr
        assert "ran-once" in child.stdout
        dead = 999999
        Path(lock).write_text(f"{dead}\n", encoding="utf-8")
        old = time.time() - 60
        os.utime(lock, (old, old))
        handle, holder, reclaimed = acquire(lock, stale=10)
        assert handle is not None and reclaimed == dead, (holder, reclaimed)
        release(handle)
        assert read_pid(lock) in (None, os.getpid())
    print("self-test: ok")
    return 0


def main():
    if "--self-test" in sys.argv[1:]:
        return self_test()
    raw, words = split_argv(sys.argv[1:])
    parser = argparse.ArgumentParser(
        description="Hold an exclusive flock while a command runs; fail with 75 if a copy is active."
    )
    parser.add_argument("--lock", metavar="FILE", help="lock file path (default: hashed name in the runtime dir)")
    parser.add_argument("--timeout", type=float, default=0.0, help="seconds to wait for the lock (default 0)")
    parser.add_argument("--stale", type=float, default=0.0,
                        help="minimum age in seconds before dead-pid metadata is reported as stale")
    parser.add_argument("--shell", action="store_true", help="run the command through /bin/sh")
    parser.add_argument("--verbose", action="store_true", help="print lock activity to stderr")
    args = parser.parse_args(raw)
    if not words:
        parser.error("no command given (usage: single_instance.py [options] -- CMD...)")
    if args.timeout < 0 or args.stale < 0:
        parser.error("--timeout and --stale must be >= 0")
    path = args.lock or default_lock(words)
    try:
        handle, holder, reclaimed = acquire(path, args.timeout, args.stale)
    except OSError as exc:
        print(f"single-instance: cannot use lock {path}: {exc}", file=sys.stderr)
        return 2
    if handle is None:
        detail = f", holder pid {holder}" if holder else ""
        print(f"single-instance: already running{detail} ({path})", file=sys.stderr)
        return EX_TEMPFAIL
    if reclaimed is not None:
        print(f"single-instance: reclaimed stale lock from dead pid {reclaimed}", file=sys.stderr)
    if args.verbose:
        print(f"single-instance: acquired {path}", file=sys.stderr)
    try:
        if args.shell:
            return subprocess.run(" ".join(words), shell=True).returncode
        return subprocess.run(words).returncode
    except FileNotFoundError:
        print(f"single-instance: command not found: {words[0]}", file=sys.stderr)
        return 127
    finally:
        release(handle)


if __name__ == "__main__":
    sys.exit(main())
