#!/usr/bin/env python3
"""Report world-writable directories and files, noting the sticky bit."""

import argparse
import grp
import json
import os
import pwd
import stat
import sys

PSEUDO_FS = {
    "proc", "sysfs", "devtmpfs", "devpts", "cgroup", "cgroup2", "securityfs",
    "debugfs", "tracefs", "configfs", "fusectl", "mqueue", "pstore",
    "bpf", "autofs", "binfmt_misc", "rpc_pipefs", "nsfs", "tmpfs", "ramfs",
}


def pseudo_mountpoints():
    points = set()
    try:
        with open("/proc/mounts", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                parts = line.split()
                if len(parts) >= 3 and parts[2] in PSEUDO_FS:
                    points.add(os.path.realpath(parts[1].replace("\\040", " ")))
    except OSError:
        pass
    return points


def owner_name(uid, gid):
    try:
        user = pwd.getpwuid(uid).pw_name
    except KeyError:
        user = str(uid)
    try:
        group = grp.getgrgid(gid).gr_name
    except KeyError:
        group = str(gid)
    return user, group


def scan(roots, include_sticky):
    mounts = pseudo_mountpoints()
    findings = []
    errors = []
    scanned = 0
    seen = set()

    def on_error(exc):
        errors.append(str(exc))

    for root in roots:
        if not os.path.exists(root):
            errors.append("no such path: %s" % root)
            continue
        for dirpath, dirnames, filenames in os.walk(root, onerror=on_error):
            dirnames[:] = sorted(
                d for d in dirnames
                if os.path.realpath(os.path.join(dirpath, d)) not in mounts)
            candidates = [(dirpath, True)]
            candidates += [(os.path.join(dirpath, name), False) for name in filenames]
            for full, is_dir in candidates:
                try:
                    st = os.lstat(full)
                except OSError as exc:
                    errors.append(str(exc))
                    continue
                if stat.S_ISLNK(st.st_mode):
                    continue
                if is_dir and not stat.S_ISDIR(st.st_mode):
                    continue
                if not is_dir and not stat.S_ISREG(st.st_mode):
                    continue
                key = (st.st_dev, st.st_ino)
                if key in seen:
                    continue
                seen.add(key)
                scanned += 1
                if not (st.st_mode & stat.S_IWOTH):
                    continue
                if is_dir and not include_sticky and (st.st_mode & stat.S_ISVTX):
                    continue
                user, group = owner_name(st.st_uid, st.st_gid)
                findings.append({
                    "path": os.path.abspath(full),
                    "type": "dir" if is_dir else "file",
                    "mode": stat.filemode(st.st_mode),
                    "octal": oct(stat.S_IMODE(st.st_mode)),
                    "owner": user,
                    "group": group,
                    "sticky": bool(st.st_mode & stat.S_ISVTX) if is_dir else False,
                })
    findings.sort(key=lambda row: (row["type"], row["path"]))
    return scanned, findings, errors


def self_test():
    import subprocess
    import tempfile

    script = os.path.abspath(__file__)
    with tempfile.TemporaryDirectory() as tmp:
        plain_dir = os.path.join(tmp, "plain")
        sticky_dir = os.path.join(tmp, "sticky")
        os.makedirs(plain_dir)
        os.makedirs(sticky_dir)
        open_file = os.path.join(tmp, "open.txt")
        closed_file = os.path.join(tmp, "closed.txt")
        for path in (open_file, closed_file):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("x\n")
        os.chmod(plain_dir, 0o777)
        os.chmod(sticky_dir, 0o1777)
        os.chmod(open_file, 0o666)
        os.chmod(closed_file, 0o644)

        result = subprocess.run([sys.executable, script, "--json", tmp],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        rows = json.loads(result.stdout)["findings"]
        by_path = {row["path"]: row for row in rows}
        assert plain_dir in by_path and open_file in by_path, by_path
        assert closed_file not in by_path
        assert sticky_dir not in by_path, "sticky dir should be skipped by default"
        assert by_path[plain_dir]["sticky"] is False

        result = subprocess.run([sys.executable, script, "--json", "--include-sticky", tmp],
                                capture_output=True, text=True)
        rows = json.loads(result.stdout)["findings"]
        by_path = {row["path"]: row for row in rows}
        assert sticky_dir in by_path and by_path[sticky_dir]["sticky"] is True
    print("self-test: PASS")


def main():
    ap = argparse.ArgumentParser(
        description="Report world-writable files and directories; note sticky dirs.")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--include-sticky", action="store_true",
                    help="include world-writable dirs protected by the sticky bit")
    ap.add_argument("--self-test", action="store_true", help="run built-in smoke test")
    ap.add_argument("paths", nargs="*", help="paths to scan (default: /tmp /var/tmp)")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    roots = args.paths or ["/tmp", "/var/tmp"]
    scanned, findings, errors = scan(roots, args.include_sticky)
    if errors and not scanned:
        for err in errors:
            print("error: %s" % err, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"roots": roots, "entries_scanned": scanned,
                          "include_sticky": args.include_sticky,
                          "findings": findings, "errors": errors}, indent=2))
    else:
        print("%-11s %-8s %-9s %-9s %s" %
              ("MODE", "TYPE", "OWNER", "GROUP", "PATH"))
        for row in findings:
            note = " [sticky]" if row["sticky"] else ""
            print("%-11s %-8s %-9.9s %-9.9s %s%s" %
                  (row["mode"], row["type"], row["owner"], row["group"],
                   row["path"], note))
        print("\n%d world-writable entr(ies) among %d scanned" %
              (len(findings), scanned))
        print("world-writable directories with the sticky bit are skipped "
              "unless --include-sticky is given")
        for err in errors:
            print("warning: %s" % err, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
