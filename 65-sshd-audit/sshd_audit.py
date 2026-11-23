#!/usr/bin/env python3
"""Audit sshd_config, following Include globs, for common weak settings."""

import argparse
import glob
import json
import os
import sys


def expand_include(pattern, base_dir):
    if not os.path.isabs(pattern):
        pattern = os.path.join(base_dir, pattern)
    return sorted(glob.glob(pattern))


def parse_config(path, directives, seen, depth=0, in_match=False):
    if depth > 16:
        return
    real = os.path.realpath(path)
    if real in seen:
        return
    seen.add(real)
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError as exc:
        directives.append(("!", "_error", str(exc), path, 0, False))
        return
    with fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            hash_pos = line.find("#")
            if hash_pos != -1:
                line = line[:hash_pos].strip()
            parts = line.split(None, 1)
            if not parts:
                continue
            key = parts[0].lower()
            value = parts[1].strip() if len(parts) > 1 else ""
            if key == "match":
                in_match = True
                directives.append((key, value, path, lineno, True))
                continue
            if key == "include":
                for include_path in expand_include(value.strip('"'), os.path.dirname(real)):
                    parse_config(include_path, directives, seen, depth + 1, in_match)
                continue
            directives.append((key, value, path, lineno, in_match))


def check(directives):
    findings = []
    info = []

    def add(severity, key, value, path, line, message):
        findings.append({"severity": severity, "key": key, "value": value,
                         "file": path, "line": line, "message": message})

    global_first = {}
    for key, value, path, line, in_match in directives:
        if in_match or key == "match":
            continue
        if key not in global_first:
            global_first[key] = (value, path, line)

    def get(key):
        return global_first.get(key)

    root = get("permitrootlogin")
    if root:
        value = root[0].lower()
        if value == "yes":
            add("high", "PermitRootLogin", root[0], root[1], root[2],
                "root may log in with a password or key")
        elif value in ("prohibit-password", "without-password"):
            info.append("PermitRootLogin=%s: key-only root login" % root[0])
        elif value == "forced-commands-only":
            add("medium", "PermitRootLogin", root[0], root[1], root[2],
                "root login allowed for forced commands")
        elif value != "no":
            add("medium", "PermitRootLogin", root[0], root[1], root[2],
                "unrecognized value")
    else:
        info.append("PermitRootLogin not set (OpenSSH default: prohibit-password)")

    pwauth = get("passwordauthentication")
    if pwauth and pwauth[0].lower() == "yes":
        add("medium", "PasswordAuthentication", pwauth[0], pwauth[1], pwauth[2],
            "password authentication is enabled")
    elif pwauth:
        info.append("PasswordAuthentication=%s" % pwauth[0])
    else:
        info.append("PasswordAuthentication not set (often defaults to yes)")

    empty = get("permitemptypasswords")
    if empty and empty[0].lower() == "yes":
        add("critical", "PermitEmptyPasswords", empty[0], empty[1], empty[2],
            "empty passwords are accepted")
    elif not empty:
        info.append("PermitEmptyPasswords not set (default: no)")

    pubkey = get("pubkeyauthentication")
    if pubkey and pubkey[0].lower() == "no":
        add("medium", "PubkeyAuthentication", pubkey[0], pubkey[1], pubkey[2],
            "public-key authentication is disabled")

    tries = get("maxauthtries")
    if tries:
        try:
            if int(tries[0]) > 6:
                add("low", "MaxAuthTries", tries[0], tries[1], tries[2],
                    "more than six authentication attempts allowed")
        except ValueError:
            add("low", "MaxAuthTries", tries[0], tries[1], tries[2],
                "value is not an integer")

    x11 = get("x11forwarding")
    if x11 and x11[0].lower() == "yes":
        add("low", "X11Forwarding", x11[0], x11[1], x11[2],
            "X11 forwarding increases attack surface")

    hostbased = get("hostbasedauthentication")
    if hostbased and hostbased[0].lower() == "yes":
        add("medium", "HostbasedAuthentication", hostbased[0], hostbased[1],
            hostbased[2], "host-based authentication is enabled")

    ignorerhosts = get("ignorerhosts")
    if ignorerhosts and ignorerhosts[0].lower() == "no":
        add("low", "IgnoreRhosts", ignorerhosts[0], ignorerhosts[1],
            ignorerhosts[2], "rhosts files are trusted")

    protocol = get("protocol")
    if protocol and "1" in protocol[0].split(","):
        add("high", "Protocol", protocol[0], protocol[1], protocol[2],
            "SSH protocol 1 is obsolete")

    errors = [row for row in directives if row[0] == "!"]
    return findings, info, errors


def self_test():
    import subprocess
    import tempfile

    script = os.path.abspath(__file__)
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "conf.d"))
        with open(os.path.join(tmp, "conf.d", "extra.conf"), "w", encoding="utf-8") as fh:
            fh.write("PubkeyAuthentication no\nX11Forwarding yes\n")
        config = os.path.join(tmp, "sshd_config")
        with open(config, "w", encoding="utf-8") as fh:
            fh.write("Include conf.d/*.conf\n")
            fh.write("PermitRootLogin yes\n")
            fh.write("PasswordAuthentication no\n")
            fh.write("PermitEmptyPasswords yes\n")
            fh.write("MaxAuthTries 10\n")
            fh.write("Match User backup\n")
            fh.write("    PasswordAuthentication yes\n")
        result = subprocess.run([sys.executable, script, "--json", config],
                                capture_output=True, text=True)
        assert result.returncode == 1, result.stdout + result.stderr
        report = json.loads(result.stdout)
        keys = {row["key"] for row in report["findings"]}
        assert {"PermitRootLogin", "PermitEmptyPasswords", "PubkeyAuthentication",
                "X11Forwarding", "MaxAuthTries"} <= keys, keys
        assert report["counts"].get("critical") == 1, report["counts"]
        match_hits = [row for row in report["findings"]
                      if row["key"] == "PasswordAuthentication"]
        assert not match_hits, "Match-block PasswordAuthentication must be ignored"
        clean = os.path.join(tmp, "clean.conf")
        with open(clean, "w", encoding="utf-8") as fh:
            fh.write("PermitRootLogin no\nPasswordAuthentication no\n"
                     "PermitEmptyPasswords no\nPubkeyAuthentication yes\n")
        result = subprocess.run([sys.executable, script, clean],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stdout
    print("self-test: PASS")


def main():
    ap = argparse.ArgumentParser(
        description="Audit sshd_config and its Include files for weak settings.")
    ap.add_argument("config", nargs="?", default="/etc/ssh/sshd_config")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--self-test", action="store_true", help="run built-in smoke test")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not os.path.isfile(args.config):
        print("error: config not found: %s" % args.config, file=sys.stderr)
        return 2
    directives = []
    parse_config(args.config, directives, set())
    findings, info, errors = check(directives)
    counts = {}
    for row in findings:
        counts[row["severity"]] = counts.get(row["severity"], 0) + 1
    if errors:
        print("error: cannot read %s" % errors[0][2], file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"config": os.path.abspath(args.config),
                          "findings": findings, "counts": counts,
                          "notes": info, "files_parsed": len(set(
                              row[2] for row in directives))}, indent=2))
    else:
        print("config: %s" % os.path.abspath(args.config))
        for row in findings:
            print("%-8s %s=%s (%s:%d) %s" %
                  (row["severity"].upper(), row["key"], row["value"],
                   row["file"], row["line"], row["message"]))
        for note in info:
            print("info     %s" % note)
        summary = ", ".join("%s=%d" % (sev, counts[sev]) for sev in
                            ("critical", "high", "medium", "low") if sev in counts)
        print("\n%d finding(s)%s" % (len(findings), ": " + summary if summary else ""))
        print("Match-block directives are parsed but not audited as global policy")
    return 1 if any(row["severity"] in ("critical", "high") for row in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
