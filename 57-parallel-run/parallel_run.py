#!/usr/bin/env python3
"""Run shell commands from a file with a concurrency limit and capture results."""
import argparse
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def as_text(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def load_commands(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"no such file: {path}")
    entries = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        entries.append((number, text))
    return entries


def run_one(number, command, timeout):
    started = time.monotonic()
    try:
        proc = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        code = 124
        stdout = as_text(exc.stdout)
        stderr = as_text(exc.stderr) + ("\n" if exc.stderr else "") + f"timed out after {timeout}s"
    except OSError as exc:
        code, stdout, stderr = 127, "", str(exc)
    return {
        "number": number,
        "command": command,
        "exit": code,
        "stdout": as_text(stdout),
        "stderr": as_text(stderr),
        "seconds": time.monotonic() - started,
    }


def run_parallel(entries, jobs=4, timeout=None, out=print, show_output=True):
    if not entries:
        return []
    results = [None] * len(entries)
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = {
            pool.submit(run_one, number, command, timeout): index
            for index, (number, command) in enumerate(entries)
        }
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    for result in results:
        status = "ok" if result["exit"] == 0 else "FAIL"
        out(f"[{result['number']}] {result['command']}")
        out(f"    {status} exit={result['exit']} {result['seconds']:.3f}s")
        if show_output:
            for line in result["stdout"].rstrip().splitlines():
                out(f"    | {line}")
            for line in result["stderr"].rstrip().splitlines():
                out(f"    ! {line}")
    failed = [result for result in results if result["exit"] != 0]
    out(f"summary: {len(results)} commands, {len(results) - len(failed)} ok, {len(failed)} failed")
    if failed:
        out("failed: " + ", ".join(f"[{result['number']}]" for result in failed))
    return results


def self_test():
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "commands.txt"
        path.write_text(
            "# a comment\n\necho one\nexit 3\necho later\n", encoding="utf-8"
        )
        entries = load_commands(path)
        assert [number for number, command in entries] == [3, 4, 5], entries
        lines = []
        results = run_parallel(entries, jobs=2, timeout=5, out=lines.append)
        assert [result["exit"] for result in results] == [0, 3, 0], results
        assert results[0]["stdout"].strip() == "one"
        assert any("summary: 3 commands, 2 ok, 1 failed" in line for line in lines), lines
        assert any(line.startswith("[4]") for line in lines)
        results = run_parallel([(9, "sleep 2")], jobs=1, timeout=0.2, out=lambda line: None)
        assert results[0]["exit"] == 124, results[0]
        try:
            load_commands(Path(td) / "missing.txt")
            raise AssertionError("missing command file must fail")
        except FileNotFoundError:
            pass
    print("self-test: ok")
    return 0


def main():
    if "--self-test" in sys.argv[1:]:
        return self_test()
    parser = argparse.ArgumentParser(description="Run commands from a file with limited parallelism.")
    parser.add_argument("file", help="text file with one shell command per line; # lines are ignored")
    parser.add_argument("--jobs", type=int, default=4, help="maximum concurrent commands (default 4)")
    parser.add_argument("--timeout", type=float, help="per-command timeout in seconds")
    parser.add_argument("--quiet", action="store_true", help="hide captured stdout/stderr")
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be at least 1")
    if args.timeout is not None and args.timeout <= 0:
        parser.error("--timeout must be > 0")
    try:
        entries = load_commands(args.file)
    except (OSError, UnicodeError) as exc:
        print(f"parallel-run: {exc}", file=sys.stderr)
        return 2
    if not entries:
        print("parallel-run: no commands found in file", file=sys.stderr)
        return 2
    results = run_parallel(entries, args.jobs, args.timeout, show_output=not args.quiet)
    return 1 if any(result["exit"] != 0 for result in results) else 0


if __name__ == "__main__":
    sys.exit(main())
