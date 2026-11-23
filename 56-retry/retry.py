#!/usr/bin/env python3
"""Run a command with bounded retries, exponential backoff, and jitter."""
import argparse
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def backoff(attempt, base, factor, max_delay, jitter, rng=random):
    delay = min(max_delay, base * (factor ** (attempt - 1)))
    if jitter:
        delay += rng.uniform(-jitter * delay, jitter * delay)
    return max(0.0, delay)


def split_argv(argv):
    if "--" in argv:
        index = argv.index("--")
        return argv[:index], argv[index + 1:]
    return argv, []


def run_with_retry(command, attempts=3, base=0.5, factor=2.0, max_delay=30.0,
                   jitter=0.1, shell=False, sleep=time.sleep, out=print):
    codes = []
    for attempt in range(1, attempts + 1):
        started = time.monotonic()
        try:
            proc = subprocess.run(command, shell=shell)
            code = proc.returncode
        except FileNotFoundError:
            out(f"command not found: {command[0] if isinstance(command, list) else command}")
            code = 127
        except OSError as exc:
            out(f"failed to execute: {exc}")
            code = 126
        elapsed = time.monotonic() - started
        codes.append(code)
        out(f"[{now()}] attempt {attempt}/{attempts}: exit {code} ({elapsed:.3f}s)")
        if code == 0:
            out(f"ok after {attempt} attempt(s)")
            return 0, codes
        if attempt < attempts:
            delay = backoff(attempt, base, factor, max_delay, jitter)
            out(f"retrying in {delay:.2f}s")
            sleep(delay)
    out(f"giving up after {attempts} attempt(s); last exit {codes[-1]}")
    return codes[-1], codes


def self_test():
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        counter = str(Path(td) / "count.txt")
        script = str(Path(td) / "flaky.py")
        with open(script, "w", encoding="utf-8") as handle:
            handle.write(
                "import pathlib, sys\n"
                f"p = pathlib.Path({counter!r})\n"
                "n = int(p.read_text()) + 1 if p.exists() else 1\n"
                "p.write_text(str(n))\n"
                "sys.exit(0 if n >= 3 else 1)\n"
            )
        quiet = lambda line: None
        code, codes = run_with_retry(
            [sys.executable, script], attempts=5, base=0.001, factor=2.0,
            jitter=0.0, sleep=lambda seconds: None, out=quiet,
        )
        assert code == 0 and codes == [1, 1, 0], (code, codes)
        code, codes = run_with_retry(
            [sys.executable, "-c", "raise SystemExit(4)"], attempts=2, base=0,
            jitter=0.0, sleep=lambda seconds: None, out=quiet,
        )
        assert code == 4 and codes == [4, 4], (code, codes)
        assert backoff(1, 1.0, 2.0, 100, 0) == 1.0
        assert backoff(4, 1.0, 2.0, 5, 0) == 5.0
        delay = backoff(2, 2.0, 3.0, 100, 0.5, rng=random.Random(1))
        assert 3.0 <= delay <= 9.0, delay
    print("self-test: ok")
    return 0


def main():
    if "--self-test" in sys.argv[1:]:
        return self_test()
    raw, words = split_argv(sys.argv[1:])
    parser = argparse.ArgumentParser(description="Retry a command with exponential backoff and jitter.")
    parser.add_argument("--max", dest="attempts", type=int, default=3, help="total attempts (default 3)")
    parser.add_argument("--base", type=float, default=0.5, help="first delay in seconds (default 0.5)")
    parser.add_argument("--factor", type=float, default=2.0, help="delay multiplier (default 2)")
    parser.add_argument("--max-delay", type=float, default=30.0, help="delay ceiling in seconds (default 30)")
    parser.add_argument("--jitter", type=float, default=0.1, help="random fraction added to delay (default 0.1)")
    parser.add_argument("--shell", action="store_true", help="run the command through /bin/sh")
    args = parser.parse_args(raw)
    if not words:
        parser.error("no command given (usage: retry.py [options] -- CMD...)")
    if args.attempts < 1:
        parser.error("--max must be at least 1")
    if args.base < 0 or args.max_delay < 0:
        parser.error("--base and --max-delay must be >= 0")
    if args.factor < 1:
        parser.error("--factor must be >= 1")
    if not 0 <= args.jitter <= 1:
        parser.error("--jitter must be between 0 and 1")
    command = " ".join(words) if args.shell else words
    code, _ = run_with_retry(
        command, args.attempts, args.base, args.factor, args.max_delay,
        args.jitter, args.shell,
    )
    return code


if __name__ == "__main__":
    sys.exit(main())
