#!/usr/bin/env python3
"""Report filesystem usage from /proc/self/mounts and flag full filesystems."""

import argparse
import json
import os
import sys

PSEUDO_FS = {
    "proc", "sysfs", "devtmpfs", "devpts", "cgroup", "cgroup2", "securityfs",
    "debugfs", "tracefs", "configfs", "fusectl", "mqueue", "hugetlbfs",
    "pstore", "bpf", "autofs", "binfmt_misc", "rpc_pipefs", "nsfs",
    "efivarfs", "squashfs", "ramfs", "tmpfs",
}


def unescape(field):
    """Decode the octal escapes used in /proc/self/mounts."""
    for code, char in ((r"\040", " "), (r"\011", "\t"), (r"\012", "\n"), (r"\134", "\\")):
        field = field.replace(code, char)
    return field


def parse_mounts(text):
    """Yield (device, mountpoint, fstype) from mount table text."""
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        yield parts[0], unescape(parts[1]), parts[2]


def usage(mountpoint):
    """Return size figures for a mountpoint, or None when it cannot be stat'd."""
    try:
        st = os.statvfs(mountpoint)
    except OSError:
        return None
    total = st.f_blocks * st.f_frsize
    free = st.f_bfree * st.f_frsize
    avail = st.f_bavail * st.f_frsize
    used = total - free
    percent = (100.0 * used / total) if total else 0.0
    return {
        "size": total,
        "used": used,
        "available": avail,
        "percent": round(percent, 1),
    }


def classify(percent, warn, crit):
    if percent >= crit:
        return "critical"
    if percent >= warn:
        return "warning"
    return "ok"


def human(n):
    value = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB"):
        if abs(value) < 1024 or unit == "PiB":
            return f"{int(value)} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} PiB"


def fit(text, width):
    return text if len(text) <= width else text[: width - 3] + "..."


def collect(warn, crit):
    """Return one record per unique real filesystem, sorted by mountpoint."""
    with open("/proc/self/mounts", encoding="utf-8", errors="replace") as fh:
        mounts = list(parse_mounts(fh.read()))
    records = []
    seen = set()
    for device, mountpoint, fstype in mounts:
        if fstype in PSEUDO_FS or fstype == "selinuxfs" or fstype.startswith("fuse."):
            continue
        try:
            dev_id = os.stat(mountpoint).st_dev
        except OSError:
            continue
        if dev_id in seen:
            continue
        info = usage(mountpoint)
        if info is None or info["size"] == 0:
            continue
        seen.add(dev_id)
        records.append({
            "mount": mountpoint,
            "device": device,
            "fstype": fstype,
            **info,
            "status": classify(info["percent"], warn, crit),
        })
    records.sort(key=lambda r: r["mount"])
    return records


def render(records):
    header = (f"{'MOUNT':24} {'DEVICE':20} {'TYPE':8} {'SIZE':9} "
              f"{'USED':9} {'AVAIL':9} {'USE%':5} STATUS")
    lines = [header]
    for r in records:
        lines.append(
            f"{fit(r['mount'], 24):24} {fit(r['device'], 20):20} "
            f"{fit(r['fstype'], 8):8} {human(r['size']):>9} "
            f"{human(r['used']):>9} {human(r['available']):>9} "
            f"{r['percent']:>4.1f}% {r['status']}"
        )
    return "\n".join(lines)


def self_test():
    assert unescape(r"/mnt/with\040space") == "/mnt/with space"
    got = list(parse_mounts("dev /mnt/x ext4 rw 0 0\nbroken line\n"))
    assert got == [("dev", "/mnt/x", "ext4")], got
    assert classify(50, 85, 95) == "ok"
    assert classify(85, 85, 95) == "warning"
    assert classify(99.9, 85, 95) == "critical"
    info = usage("/")
    assert info is not None and 0 <= info["percent"] <= 100, info
    assert human(0) == "0 B" and human(1536) == "1.5 KiB"
    assert "MOUNT" in render([])
    print("self-test OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--warn", type=float, default=85.0, help="warning threshold %% (default 85)")
    ap.add_argument("--crit", type=float, default=95.0, help="critical threshold %% (default 95)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    ap.add_argument("--self-test", action="store_true", help="run offline self tests")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not (0 <= args.warn < args.crit <= 100):
        ap.error("thresholds must satisfy 0 <= warn < crit <= 100")

    try:
        records = collect(args.warn, args.crit)
    except OSError as exc:
        print(f"disk-alert: cannot read mounts: {exc}", file=sys.stderr)
        return 3

    if args.json:
        print(json.dumps({"filesystems": records}, indent=2, sort_keys=True))
    else:
        print(render(records))

    if any(r["status"] == "critical" for r in records):
        return 2
    if any(r["status"] == "warning" for r in records):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
