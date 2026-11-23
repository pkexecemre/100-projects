#!/usr/bin/env python3
"""Size-based log rotation with numbered backups and atomic renames."""
import argparse
import os
import re
import sys
from pathlib import Path


def parse_size(text):
    units = {"k": 1024, "m": 1024 ** 2, "g": 1024 ** 3}
    raw = text.strip().lower()
    multiplier = 1
    if raw and raw[-1] in units:
        multiplier = units[raw[-1]]
        raw = raw[:-1]
    try:
        value = int(float(raw) * multiplier)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid size: {text!r}")
    if value < 1:
        raise argparse.ArgumentTypeError("size must be at least 1 byte")
    return value


def backup_path(path, index):
    return path.with_name(f"{path.name}.{index}")


def backups(path):
    pattern = re.compile(re.escape(path.name) + r"\.(\d+)$")
    found = []
    for entry in path.parent.iterdir():
        match = pattern.fullmatch(entry.name)
        if match and entry.is_file():
            found.append((int(match.group(1)), entry))
    return sorted(found)


def rotate(path, max_bytes, keep=5, dry_run=False, out=print):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"no such file: {path}")
    if keep < 1:
        raise ValueError("--keep must be at least 1")
    size = path.stat().st_size
    if size < max_bytes:
        out(f"below threshold: {path} is {size} bytes (limit {max_bytes})")
        return None

    actions = []
    for index, entry in backups(path):
        if index >= keep:
            actions.append(("remove", entry, None))
    for index in range(keep - 1, 0, -1):
        source = backup_path(path, index)
        if source.exists():
            actions.append(("move", source, backup_path(path, index + 1)))
    actions.append(("move", path, backup_path(path, 1)))

    if dry_run:
        for action, source, target in actions:
            if action == "remove":
                out(f"would remove {source.name}")
            else:
                out(f"would move {source.name} -> {target.name}")
        return {"dry_run": True, "size": size, "actions": actions}

    mode = path.stat().st_mode & 0o7777
    for action, source, target in actions:
        if action == "remove":
            if source.exists():
                source.unlink()
        else:
            os.replace(source, target)
    path.touch()
    os.chmod(path, mode)
    out(f"rotated {path.name} ({size} bytes) -> {backup_path(path, 1).name}")
    return {"dry_run": False, "size": size, "backup": backup_path(path, 1)}


def self_test():
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        log = Path(td) / "app.log"
        log.write_text("x" * 100, encoding="utf-8")
        quiet = lambda line: None
        assert rotate(log, 50, keep=2, out=quiet)["size"] == 100
        assert log.stat().st_size == 0
        assert (Path(td) / "app.log.1").read_text() == "x" * 100
        assert rotate(log, 50, keep=2, out=quiet) is None
        log.write_text("y" * 100, encoding="utf-8")
        rotate(log, 50, keep=2, out=quiet)
        names = sorted(p.name for p in Path(td).iterdir())
        assert names == ["app.log", "app.log.1", "app.log.2"], names
        assert (Path(td) / "app.log.2").read_text() == "x" * 100
        assert (Path(td) / "app.log.1").read_text() == "y" * 100
        log.write_text("z" * 100, encoding="utf-8")
        dry = rotate(log, 50, keep=1, dry_run=True, out=quiet)
        assert dry["dry_run"] and (Path(td) / "app.log.1").read_text() == "y" * 100
        assert (Path(td) / "app.log.2").exists()
        rotate(log, 50, keep=1, out=quiet)
        names = sorted(p.name for p in Path(td).iterdir())
        assert names == ["app.log", "app.log.1"], names
        assert log.stat().st_size == 0
        assert (Path(td) / "app.log.1").read_text() == "z" * 100
        assert parse_size("2K") == 2048 and parse_size("1.5M") == 1572864
        try:
            parse_size("nope")
            raise AssertionError("bad size must fail")
        except argparse.ArgumentTypeError:
            pass
    print("self-test: ok")
    return 0


def main():
    if "--self-test" in sys.argv[1:]:
        return self_test()
    parser = argparse.ArgumentParser(description="Rotate a log file once it reaches a size limit.")
    parser.add_argument("file", help="log file to check and rotate")
    parser.add_argument("--max-bytes", type=parse_size, default=1048576,
                        metavar="SIZE", help="rotate at this size; accepts K/M/G (default 1M)")
    parser.add_argument("--keep", type=int, default=5, help="number of numbered backups (default 5)")
    parser.add_argument("--dry-run", action="store_true", help="show renames without touching files")
    args = parser.parse_args()
    if args.keep < 1:
        parser.error("--keep must be at least 1")
    try:
        rotate(args.file, args.max_bytes, args.keep, args.dry_run)
    except (OSError, ValueError) as exc:
        print(f"log-rotate: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
