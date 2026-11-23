#!/usr/bin/env python3
"""Neofetch-style system summary using only the standard library."""
import argparse
import json
import os
import platform
import shutil
import sys
import time

LOGO = [
    "      .--.      ",
    "     |o_o |     ",
    "     |:_/ |     ",
    "    //   \\ \\    ",
    "   (|     | )   ",
    "  /'\\_   _/`\\  ",
    "  \\___)=(___/   ",
]


def read_os_release() -> dict[str, str]:
    data = {}
    try:
        with open("/etc/os-release", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                key, sep, value = line.strip().partition("=")
                if sep:
                    data[key] = value.strip().strip('"')
    except OSError:
        pass
    return data


def cpu_model() -> tuple[str, int]:
    model = ""
    try:
        with open("/proc/cpuinfo", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if line.lower().startswith("model name"):
                    model = line.split(":", 1)[1].strip()
                    break
    except OSError:
        pass
    return model or platform.processor() or "unknown", os.cpu_count() or 1


def memory() -> tuple[int | None, int | None]:
    values = {}
    try:
        with open("/proc/meminfo", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                key, _, rest = line.partition(":")
                if key in ("MemTotal", "MemAvailable"):
                    values[key] = int(rest.split()[0]) * 1024
    except (OSError, ValueError, IndexError):
        return None, None
    total = values.get("MemTotal")
    available = values.get("MemAvailable")
    if total is None:
        return None, None
    return total, total - available if available is not None else None


def uptime_seconds() -> float | None:
    try:
        with open("/proc/uptime", encoding="utf-8") as handle:
            return float(handle.readline().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def human_bytes(size: int | None) -> str:
    if size is None:
        return "unknown"
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TiB"


def human_uptime(seconds: float | None) -> str:
    if seconds is None:
        return "unknown"
    days, rest = divmod(int(seconds), 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    if days:
        return f"{days}d {hours}h {minutes}m"
    return f"{hours}h {minutes}m"


def collect() -> dict:
    osr = read_os_release()
    model, cores = cpu_model()
    mem_total, mem_used = memory()
    disk = shutil.disk_usage("/")
    up = uptime_seconds()
    return {
        "os": osr.get("PRETTY_NAME") or f"{platform.system()} {platform.release()}",
        "kernel": platform.release(),
        "arch": platform.machine() or "unknown",
        "host": platform.node() or "unknown",
        "cpu": model,
        "cores": cores,
        "memory_total": human_bytes(mem_total),
        "memory_used": human_bytes(mem_used),
        "memory_percent": round(mem_used * 100 / mem_total) if mem_total and mem_used else None,
        "uptime": human_uptime(up),
        "uptime_seconds": round(up) if up is not None else None,
        "disk_total": human_bytes(disk.total),
        "disk_used": human_bytes(disk.used),
        "disk_percent": round(disk.used * 100 / disk.total) if disk.total else None,
        "python": platform.python_version(),
    }


def render(info: dict, logo: bool = True) -> str:
    lines = [
        f"OS: {info['os']}",
        f"Kernel: {info['kernel']}",
        f"Arch: {info['arch']}",
        f"Host: {info['host']}",
        f"CPU: {info['cpu']} ({info['cores']} cores)",
        f"Memory: {info['memory_used']} / {info['memory_total']}"
        + (f" ({info['memory_percent']}%)" if info["memory_percent"] is not None else ""),
        f"Uptime: {info['uptime']}",
        f"Disk: {info['disk_used']} / {info['disk_total']} ({info['disk_percent']}%)",
        f"Python: {info['python']}",
    ]
    if not logo:
        return "\n".join(lines)
    width = max(len(row) for row in LOGO)
    rows = []
    for i in range(max(len(LOGO), len(lines))):
        left = LOGO[i] if i < len(LOGO) else " " * width
        right = lines[i] if i < len(lines) else ""
        rows.append(f"{left:<{width}}  {right}".rstrip())
    return "\n".join(rows)


def self_test() -> None:
    info = collect()
    required = {"os", "kernel", "arch", "host", "cpu", "cores", "memory_total",
                "memory_used", "uptime", "disk_total", "disk_used", "python"}
    assert required <= info.keys(), required - info.keys()
    assert info["cores"] >= 1
    assert info["uptime_seconds"] is None or info["uptime_seconds"] >= 0
    text = render(info)
    for label in ("OS:", "Kernel:", "CPU:", "Memory:", "Uptime:", "Disk:"):
        assert label in text
    assert json.loads(json.dumps(info)) == info
    assert "OS:" in render(info, logo=False)
    print("self-test: ok (system info collected and rendered)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Neofetch-style system summary.")
    ap.add_argument("--json", action="store_true", help="print collected data as JSON")
    ap.add_argument("--no-logo", action="store_true", help="skip the ASCII logo")
    ap.add_argument("--self-test", action="store_true", help="run internal checks and exit")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    try:
        info = collect()
    except OSError as exc:
        print(f"sysfetch: could not read system data: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(info, indent=2))
    else:
        print(render(info, logo=not args.no_logo))
    return 0


if __name__ == "__main__":
    sys.exit(main())
