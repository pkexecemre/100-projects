#!/usr/bin/env python3
"""Time a command: wall clock, user and sys CPU, exit status, optional repeats."""
import argparse
import json
import resource
import statistics
import subprocess
import sys
import time


def split_argv(argv):
    if "--" in argv:
        index = argv.index("--")
        return argv[:index], argv[index + 1:]
    return argv, []


def measure(command, shell=False):
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = time.perf_counter()
    error = None
    try:
        proc = subprocess.run(command, shell=shell)
        code = proc.returncode
    except FileNotFoundError:
        code, error = 127, "command not found"
    except OSError as exc:
        code, error = 126, str(exc)
    wall = time.perf_counter() - started
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {
        "exit": code,
        "error": error,
        "wall": wall,
        "user": max(0.0, after.ru_utime - before.ru_utime),
        "sys": max(0.0, after.ru_stime - before.ru_stime),
    }


def summarize(runs):
    walls = [run["wall"] for run in runs]
    return {
        "count": len(walls),
        "mean": statistics.mean(walls),
        "min": min(walls),
        "max": max(walls),
        "stdev": statistics.stdev(walls) if len(walls) > 1 else 0.0,
        "total": sum(walls),
        "user_total": sum(run["user"] for run in runs),
        "sys_total": sum(run["sys"] for run in runs),
        "exit_codes": [run["exit"] for run in runs],
    }


def report(runs, warmup=0, as_json=False, out=print):
    stats = summarize(runs)
    if as_json:
        out(json.dumps({"warmup": warmup, "runs": runs, "summary": stats}, indent=2))
        return stats
    for index, run in enumerate(runs, 1):
        note = f" ({run['error']})" if run["error"] else ""
        out(
            f"run {index}: exit {run['exit']} wall {run['wall']:.3f}s "
            f"user {run['user']:.3f}s sys {run['sys']:.3f}s{note}"
        )
    out(
        f"results: n={stats['count']} mean={stats['mean']:.3f}s min={stats['min']:.3f}s "
        f"max={stats['max']:.3f}s stdev={stats['stdev']:.3f}s total={stats['total']:.3f}s"
    )
    out(f"cpu: user={stats['user_total']:.3f}s sys={stats['sys_total']:.3f}s")
    if warmup:
        out(f"warmup runs completed: {warmup}")
    return stats


def self_test():
    run = measure([sys.executable, "-c", "import time; time.sleep(0.05)"])
    assert run["exit"] == 0 and run["error"] is None, run
    assert run["wall"] >= 0.04, run
    failed = measure([sys.executable, "-c", "raise SystemExit(3)"])
    assert failed["exit"] == 3 and failed["wall"] > 0, failed
    missing = measure(["/nonexistent/definitely-not-a-command-xyz"])
    assert missing["exit"] == 127 and missing["error"] == "command not found", missing
    stats = summarize([run, failed])
    assert stats["count"] == 2 and stats["min"] <= stats["max"]
    assert stats["exit_codes"] == [0, 3]
    assert summarize([run])["stdev"] == 0.0
    lines = []
    report([run, failed], as_json=False, out=lines.append)
    assert len(lines) == 4, lines
    payload = json.loads(json.dumps({"summary": summarize([run])}))
    assert payload["summary"]["count"] == 1
    print("self-test: ok")
    return 0


def main():
    if "--self-test" in sys.argv[1:]:
        return self_test()
    raw, words = split_argv(sys.argv[1:])
    parser = argparse.ArgumentParser(description="Measure wall, user and sys time for a command.")
    parser.add_argument("--repeat", type=int, default=1, help="timed runs (default 1)")
    parser.add_argument("--warmup", type=int, default=0, help="untimed warmup runs (default 0)")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--shell", action="store_true", help="run the command through /bin/sh")
    args = parser.parse_args(raw)
    if not words:
        parser.error("no command given (usage: timeit.py [options] -- CMD...)")
    if args.repeat < 1:
        parser.error("--repeat must be at least 1")
    if args.warmup < 0:
        parser.error("--warmup must be >= 0")
    command = " ".join(words) if args.shell else words
    for _ in range(args.warmup):
        measure(command, args.shell)
    runs = [measure(command, args.shell) for _ in range(args.repeat)]
    report(runs, args.warmup, args.json)
    failures = [run["exit"] for run in runs if run["exit"] != 0]
    return failures[0] if failures else 0


if __name__ == "__main__":
    sys.exit(main())
