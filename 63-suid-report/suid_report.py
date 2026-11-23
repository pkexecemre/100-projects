#!/usr/bin/env python3
"""Report SUID and SGID regular files under the given paths."""

import argparse
import grp
import json
import os
import pwd
import stat
import sys

PSEUDO_FS = {
    "proc", "sysfs", "devtmpfs", "devpts", "cgroup", "cgroup2", "securityfs",
    "debugfs", "tracefs", "configfs", "fusectl", "mqueue", "hugetlbfs",
    "pstore", "bpf", "autofs", "binfmt_misc", "rpc_pipefs", "nsfs",
    "tmpfs", "ramfs",
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


def name_for(uid, gid):
    try:
        user = pwd.getpwuid(uid).pw_name
    except KeyError:
        user = str(uid)
    try:
        group = grp.getgrgid(gid).gr_name
    except KeyError:
        group = str(gid)
    return user, group


def scan(roots):
    mounts = pseudo_mountpoints()
    findings = []
    errors = []
    seen = set()
    scanned = 0

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
            for filename in sorted(filenames):
                full = os.path.join(dirpath, filename)
                try:
                    st = os.lstat(full)
                except OSError as exc:
                    errors.append(str(exc))
                    continue
                if not stat.S_ISREG(st.st_mode):
                    continue
                key = (st.st_dev, st.st_ino)
                if key in seen:
                    continue
                seen.add(key)
                scanned += 1
                suid = bool(st.st_mode & stat.S_ISUID)
                sgid = bool(st.st_mode & stat.S_ISGID)
                if not (suid or sgid):
                    continue
                user, group = name_for(st.st_uid, st.st_gid)
                findings.append({
                    "path": os.path.abspath(full),
                    "mode": stat.filemode(st.st_mode),
                    "octal": oct(stat.S_IMODE(st.st_mode)),
                    "owner": user,
                    "group": group,
                    "size": st.st_size,
                    "suid": suid,
                    "sgid": sgid,
                })
    findings.sort(key=lambda row: row["path"])
    return scanned, findings, errors


def self_test():
    import subprocess
    import tempfile

    script = os.path.abspath(__file__)
    with tempfile.TemporaryDirectory() as tmp:
        normal = os.path.join(tmp, "normal")
        suid = os.path.join(tmp, "suid-bin")
        sgid = os.path.join(tmp, "sgid-bin")
        for path in (normal, suid, sgid):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("#!/bin/sh\ntrue\n")
        os.chmod(normal, 0o755)
        os.chmod(suid, 0o4755)
        os.chmod(sgid, 0o2755)
        result = subprocess.run([sys.executable, script, "--json", tmp],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        paths = {row["path"] for row in report["findings"]}
        assert suid in paths and sgid in paths, paths
        assert normal not in paths, paths
        by_path = {row["path"]: row for row in report["findings"]}
        assert by_path[suid]["suid"] and not by_path[suid]["sgid"]
        assert by_path[sgid]["sgid"] and not by_path[sgid]["suid"]
        missing = subprocess.run([sys.executable, script, "/no/such/dir"],
                                 capture_output=True, text=True)
        assert missing.returncode == 2, missing.stdout
    print("self-test: PASS")


def main():
    ap = argparse.ArgumentParser(
        description="Find SUID/SGID regular files, skipping pseudo filesystems.")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--fail-on-found", action="store_true",
                    help="exit 1 when any SUID/SGID file is found")
    ap.add_argument("--self-test", action="store_true", help="run built-in smoke test")
    ap.add_argument("paths", nargs="*", help="paths to scan (default: /usr /opt)")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    roots = args.paths or ["/usr", "/opt"]
    scanned, findings, errors = scan(roots)
    if errors and not findings and not scanned:
        for err in errors:
            print("error: %s" % err, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"roots": roots, "files_scanned": scanned,
                          "findings": findings, "errors": errors}, indent=2))
    else:
        print("%-11s %-9s %-9s %s" % ("MODE", "OWNER", "GROUP", "PATH"))
        for row in findings:
            print("%-11s %-9.9s %-9.9s %s" %
                  (row["mode"], row["owner"], row["group"], row["path"]))
        print("\n%d SUID/SGID file(s) among %d scanned" % (len(findings), scanned))
        for err in errors:
            print("warning: %s" % err, file=sys.stderr)
    return 1 if args.fail_on_found and findings else 0


if __name__ == "__main__":
    sys.exit(main())
