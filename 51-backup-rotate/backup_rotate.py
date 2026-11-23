#!/usr/bin/env python3
"""Create a tar.gz backup of a directory, keep N archives, and record a manifest."""
import argparse
import json
import os
import sys
import tarfile
import tempfile
import time
from datetime import datetime
from pathlib import Path

MANIFEST = "manifest.json"


def stamp():
    return time.strftime("%Y%m%d-%H%M%S")


def archive_name(dest, prefix):
    base = f"{prefix}-{stamp()}"
    candidate = dest / f"{base}.tar.gz"
    index = 1
    while candidate.exists():
        candidate = dest / f"{base}-{index}.tar.gz"
        index += 1
    return candidate


def archives(dest, prefix):
    return sorted(p for p in dest.glob(f"{prefix}-*.tar.gz") if p.is_file())


def load_manifest(dest):
    path = dest / MANIFEST
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"version": 1, "archives": []}
    if not isinstance(data, dict) or not isinstance(data.get("archives"), list):
        return {"version": 1, "archives": []}
    return data


def save_manifest(dest, data):
    path = dest / MANIFEST
    tmp = dest / (MANIFEST + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def make_archive(src, dest, keep=5, prefix=None, dry_run=False, out=print):
    src = Path(src).resolve()
    dest = Path(dest).resolve()
    if not src.is_dir():
        raise NotADirectoryError(f"source is not a directory: {src}")
    if keep < 1:
        raise ValueError("--keep must be at least 1")
    prefix = prefix or src.name
    target = archive_name(dest, prefix)
    counted = {"files": 0}

    def member_filter(info):
        if info.name == src.name:
            return info
        inner = info.name[len(src.name) + 1:]
        real = os.path.realpath(os.path.join(str(src), inner))
        if real == str(dest) or real.startswith(str(dest) + os.sep):
            return None
        if info.isreg():
            counted["files"] += 1
        return info

    existing = archives(dest, prefix) if dest.is_dir() else []
    planned = existing + [target]
    doomed = planned[:max(0, len(planned) - keep)]

    if dry_run:
        files = 0
        for root, dirs, names in os.walk(src):
            dirs[:] = [d for d in dirs if os.path.realpath(os.path.join(root, d)) != str(dest)]
            files += sum(1 for name in names if (Path(root) / name).is_file())
        out(f"would create {target} ({files} files)")
        for old in doomed:
            out(f"would remove {old.name}")
        return {"archive": target, "files": files, "bytes": 0, "dry_run": True}

    dest.mkdir(parents=True, exist_ok=True)
    handle, tmp_name = tempfile.mkstemp(prefix=".partial-", suffix=".tar.gz", dir=dest)
    os.close(handle)
    try:
        with tarfile.open(tmp_name, "w:gz") as tar:
            tar.add(str(src), arcname=src.name, filter=member_filter)
        os.replace(tmp_name, target)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)

    for old in doomed:
        old.unlink()
        out(f"removed {old.name}")

    data = load_manifest(dest)
    records = [r for r in data["archives"] if isinstance(r, dict)]
    records = [r for r in records if (dest / str(r.get("archive", ""))).is_file()]
    records.append({
        "archive": target.name,
        "source": str(src),
        "created": datetime.now().astimezone().isoformat(timespec="seconds"),
        "bytes": target.stat().st_size,
        "files": counted["files"],
    })
    data["archives"] = records
    save_manifest(dest, data)
    return {"archive": target, "files": counted["files"], "bytes": target.stat().st_size, "dry_run": False}


def self_test():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        src = root / "data"
        (src / "sub").mkdir(parents=True)
        (src / "a.txt").write_text("hello\n", encoding="utf-8")
        (src / "sub" / "b.txt").write_text("x\n", encoding="utf-8")
        dest = root / "backups"
        first = make_archive(src, dest, keep=1, out=lambda line: None)
        assert first["archive"].is_file() and first["files"] == 2
        second = make_archive(src, dest, keep=1, out=lambda line: None)
        kept = archives(dest, "data")
        assert len(kept) == 1 and kept[0] == second["archive"], kept
        manifest = load_manifest(dest)
        assert len(manifest["archives"]) == 1
        assert manifest["archives"][0]["archive"] == second["archive"].name
        with tarfile.open(kept[0]) as tar:
            names = tar.getnames()
        assert any(name.endswith("a.txt") for name in names)
        assert any(name.endswith("b.txt") for name in names)
        before = sorted(p.name for p in dest.iterdir())
        dry = make_archive(src, dest, keep=1, dry_run=True, out=lambda line: None)
        assert dry["dry_run"] and not dry["archive"].exists()
        assert sorted(p.name for p in dest.iterdir()) == before
    print("self-test: ok")
    return 0


def main():
    if "--self-test" in sys.argv[1:]:
        return self_test()
    parser = argparse.ArgumentParser(
        description="Back up a directory as a timestamped tar.gz and keep the newest N archives."
    )
    parser.add_argument("source", help="directory to archive")
    parser.add_argument("--dest", required=True, help="directory that holds archives and manifest.json")
    parser.add_argument("--keep", type=int, default=5, help="number of archives to retain (default 5)")
    parser.add_argument("--prefix", help="archive name prefix (default: source directory name)")
    parser.add_argument("--dry-run", action="store_true", help="show the plan without writing anything")
    args = parser.parse_args()
    if args.keep < 1:
        parser.error("--keep must be at least 1")
    try:
        result = make_archive(args.source, args.dest, args.keep, args.prefix, args.dry_run)
    except (OSError, ValueError) as exc:
        print(f"backup-rotate: {exc}", file=sys.stderr)
        return 2
    if not result["dry_run"]:
        print(f"archive: {result['archive']} ({result['bytes']} bytes, {result['files']} files)")
        print(f"manifest: {Path(args.dest).resolve() / MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
