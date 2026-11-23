#!/usr/bin/env python3
"""Report old, user-owned files in temp directories, optionally deleting them."""

import argparse
import json
import os
import stat
import sys
import time


def human(n):
    value = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{int(value)} B" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TiB"


def find_old(paths, days, uid=None, now=None):
    """Return regular files owned by uid whose mtime is older than days."""
    uid = os.getuid() if uid is None else uid
    now = time.time() if now is None else now
    cutoff = days * 86400.0
    found = []
    for root in paths:
        for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):
            dirnames.sort()
            for name in sorted(filenames):
                path = os.path.join(dirpath, name)
                try:
                    info = os.lstat(path)
                except OSError:
                    continue
                if not stat.S_ISREG(info.st_mode):
                    continue
                if info.st_uid != uid:
                    continue
                age = now - info.st_mtime
                if age > cutoff:
                    found.append({
                        "path": path,
                        "size": info.st_size,
                        "age_days": round(age / 86400.0, 2),
                    })
    found.sort(key=lambda f: f["path"])
    return found


def delete_files(files):
    deleted, freed, failed = 0, 0, []
    for item in files:
        try:
            os.unlink(item["path"])
            deleted += 1
            freed += item["size"]
        except OSError as exc:
            failed.append({"path": item["path"], "error": str(exc)})
    return {"deleted": deleted, "freed_bytes": freed, "failed": failed}


def summarize(files):
    return {"count": len(files), "bytes": sum(f["size"] for f in files)}


def self_test():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        old = os.path.join(tmp, "old.log")
        new = os.path.join(tmp, "new.log")
        with open(old, "w") as fh:
            fh.write("old" * 100)
        with open(new, "w") as fh:
            fh.write("new")
        now = time.time()
        os.utime(old, (now - 10 * 86400, now - 10 * 86400))
        os.utime(new, (now, now))

        found = find_old([tmp], 7, now=now)
        assert [f["path"] for f in found] == [old], found
        assert found[0]["size"] == 300
        assert find_old([tmp], 7, uid=os.getuid() + 1, now=now) == []
        assert find_old([tmp], 30, now=now) == []
        assert not os.path.exists(os.path.join(tmp, "missing"))

        summary = summarize(found)
        assert summary == {"count": 1, "bytes": 300}, summary
        result = delete_files(found)
        assert result["deleted"] == 1 and result["freed_bytes"] == 300
        assert not os.path.exists(old) and os.path.exists(new)
        assert result["failed"] == []
    print("self-test OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", default=["/tmp"],
                    help="directories to sweep (default /tmp)")
    ap.add_argument("--days", type=float, default=7.0,
                    help="minimum age in days (default 7)")
    ap.add_argument("--apply", action="store_true", help="delete the matching files")
    ap.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--self-test", action="store_true", help="run offline self tests")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    if args.yes and not args.apply:
        ap.error("--yes only makes sense together with --apply")
    if args.days < 0:
        ap.error("--days must be non-negative")
    missing = [p for p in args.paths if not os.path.isdir(p)]
    if missing:
        print(f"temp-sweep: not a directory: {missing[0]}", file=sys.stderr)
        return 2

    files = find_old(args.paths, args.days)
    summary = summarize(files)
    if not files:
        print(f"no files older than {args.days:g} days owned by uid {os.getuid()}")
        return 0

    if args.apply and not args.yes:
        if not sys.stdin.isatty():
            print("temp-sweep: refusing to delete without a tty; pass --yes", file=sys.stderr)
            return 2
        answer = input(f"Delete {summary['count']} file(s), "
                       f"{human(summary['bytes'])}? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print("aborted; nothing deleted")
            return 0

    result = None
    if args.apply:
        result = delete_files(files)

    if args.json:
        payload = {
            "roots": args.paths,
            "days": args.days,
            "uid": os.getuid(),
            "files": files,
            "summary": summary,
            "applied": bool(result),
        }
        if result:
            payload["result"] = result
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"{summary['count']} file(s), {human(summary['bytes'])} older than "
              f"{args.days:g} days, owned by uid {os.getuid()}")
        for item in files:
            print(f"{human(item['size']):>10}  {item['age_days']:>7.2f}d  {item['path']}")
        if result:
            print(f"\ndeleted {result['deleted']} file(s), freed {human(result['freed_bytes'])}")
            for fail in result["failed"]:
                print(f"  ! {fail['path']}: {fail['error']}", file=sys.stderr)
        else:
            print("\ndry run; nothing deleted (use --apply)")
    if result and result["failed"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
