#!/usr/bin/env python3
"""Emit a stable JSON snapshot of load, CPU, memory, uptime and mounts."""

import argparse
import json
import os
import sys
import time

PSEUDO_FS = {
    "proc", "sysfs", "devtmpfs", "devpts", "cgroup", "cgroup2", "securityfs",
    "debugfs", "tracefs", "configfs", "fusectl", "mqueue", "hugetlbfs",
    "pstore", "bpf", "autofs", "binfmt_misc", "rpc_pipefs", "nsfs",
    "efivarfs", "squashfs", "ramfs", "tmpfs",
}


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def loadavg():
    parts = read("/proc/loadavg").split()
    runnable, total = parts[3].split("/")
    return {
        "one": float(parts[0]),
        "five": float(parts[1]),
        "fifteen": float(parts[2]),
        "procs_running": int(runnable),
        "procs_total": int(total),
        "last_pid": int(parts[4]),
    }


def cpu_times():
    for line in read("/proc/stat").splitlines():
        if line.startswith("cpu "):
            values = [int(v) for v in line.split()[1:9]]
            values += [0] * (8 - len(values))
            keys = ("user", "nice", "system", "idle", "iowait", "irq", "softirq", "steal")
            return dict(zip(keys, values))
    raise OSError("/proc/stat has no aggregate cpu line")


def cpu_sample(interval):
    first = cpu_times()
    if interval > 0:
        time.sleep(interval)
    second = cpu_times()
    delta = {key: max(0, second[key] - first[key]) for key in first}
    total = sum(delta.values())
    if total <= 0:
        return {"sample_ms": round(interval * 1000), "user_percent": 0.0,
                "system_percent": 0.0, "idle_percent": 0.0, "iowait_percent": 0.0,
                "busy_percent": 0.0}
    pct = lambda n: round(100.0 * n / total, 2)
    idle = delta["idle"]
    iowait = delta["iowait"]
    return {
        "sample_ms": round(interval * 1000),
        "user_percent": pct(delta["user"] + delta["nice"]),
        "system_percent": pct(delta["system"] + delta["irq"] + delta["softirq"]),
        "idle_percent": pct(idle),
        "iowait_percent": pct(iowait),
        "busy_percent": round(100.0 * (total - idle - iowait) / total, 2),
    }


def memory():
    wanted = {
        "MemTotal": "total_bytes", "MemFree": "free_bytes",
        "MemAvailable": "available_bytes", "Buffers": "buffers_bytes",
        "Cached": "cached_bytes", "SwapTotal": "swap_total_bytes",
        "SwapFree": "swap_free_bytes",
    }
    values = {}
    for line in read("/proc/meminfo").splitlines():
        key, _, rest = line.partition(":")
        if key in wanted:
            values[wanted[key]] = int(rest.split()[0]) * 1024
    return values


def uptime():
    seconds = float(read("/proc/uptime").split()[0])
    return {"seconds": round(seconds, 2), "days": round(seconds / 86400.0, 2)}


def mounts():
    records, seen = [], set()
    for line in read("/proc/self/mounts").splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        fstype = parts[2]
        if fstype in PSEUDO_FS or fstype == "selinuxfs" or fstype.startswith("fuse."):
            continue
        mountpoint = parts[1].replace(r"\040", " ")
        try:
            dev_id = os.stat(mountpoint).st_dev
            st = os.statvfs(mountpoint)
        except OSError:
            continue
        total = st.f_blocks * st.f_frsize
        if total == 0 or dev_id in seen:
            continue
        seen.add(dev_id)
        used = (st.f_blocks - st.f_bfree) * st.f_frsize
        records.append({
            "mount": mountpoint,
            "device": parts[0],
            "fstype": fstype,
            "total_bytes": total,
            "used_bytes": used,
            "available_bytes": st.f_bavail * st.f_frsize,
            "use_percent": round(100.0 * used / total, 1) if total else 0.0,
        })
    records.sort(key=lambda r: r["mount"])
    return records


def collect(sample_ms):
    return {
        "schema": 1,
        "loadavg": loadavg(),
        "cpu": cpu_sample(sample_ms / 1000.0),
        "memory": memory(),
        "uptime": uptime(),
        "mounts": mounts(),
    }


def self_test():
    snapshot = collect(50)
    assert set(snapshot) == {"schema", "loadavg", "cpu", "memory", "uptime", "mounts"}
    assert snapshot["schema"] == 1
    assert snapshot["loadavg"]["procs_total"] > 0
    assert snapshot["memory"]["total_bytes"] > 0
    assert snapshot["uptime"]["seconds"] > 0
    cpu = snapshot["cpu"]
    for key in ("user_percent", "system_percent", "idle_percent", "busy_percent"):
        assert 0.0 <= cpu[key] <= 100.0, (key, cpu[key])
    for mount in snapshot["mounts"]:
        assert mount["total_bytes"] >= mount["used_bytes"] >= 0
        assert mount["use_percent"] <= 100.0
    text = json.dumps(snapshot, sort_keys=True)
    assert text.startswith("{") and json.loads(text) == json.loads(json.dumps(snapshot))
    print("self-test OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample-ms", type=int, default=200,
                    help="CPU sampling window in milliseconds (default 200)")
    ap.add_argument("--self-test", action="store_true", help="run offline self tests")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    if args.sample_ms < 0 or args.sample_ms > 60000:
        ap.error("--sample-ms must be between 0 and 60000")
    try:
        snapshot = collect(args.sample_ms)
    except OSError as exc:
        print(f"sysinfo-json: cannot read /proc: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(snapshot, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
