#!/usr/bin/env python3
"""Audit common shell environment variables for missing or suspicious values."""

import argparse
import json
import os
import sys


def audit(env):
    """Return a list of {check, status, message} findings."""
    checks = []

    def add(check, status, message):
        checks.append({"check": check, "status": status, "message": message})

    path = env.get("PATH", "")
    if not path:
        add("PATH", "error", "PATH is not set")
    else:
        entries = path.split(os.pathsep)
        seen = {}
        good = 0
        for idx, entry in enumerate(entries):
            label = f"PATH[{idx}]"
            if entry == "":
                add(label, "warn", "empty entry resolves to the current directory")
                continue
            if not os.path.isabs(entry):
                add(label, "warn", f"relative directory: {entry}")
            key = os.path.normpath(entry)
            if key in seen:
                add(label, "warn", f"duplicate of PATH[{seen[key]}]: {entry}")
                continue
            seen[key] = idx
            if not os.path.exists(entry):
                add(label, "warn", f"missing directory: {entry}")
            elif not os.path.isdir(entry):
                add(label, "warn", f"not a directory: {entry}")
            elif not os.access(entry, os.X_OK):
                add(label, "warn", f"directory is not searchable: {entry}")
            else:
                good += 1
        add("PATH", "ok" if good == len(entries) else "warn",
            f"{len(entries)} entries, {good} usable, {len(seen)} unique")

    home = env.get("HOME", "")
    if not home:
        add("HOME", "error", "HOME is not set")
    elif not os.path.exists(home):
        add("HOME", "error", f"HOME does not exist: {home}")
    elif not os.path.isdir(home):
        add("HOME", "error", f"HOME is not a directory: {home}")
    elif not os.access(home, os.W_OK):
        add("HOME", "warn", f"HOME is not writable: {home}")
    else:
        add("HOME", "ok", home)

    shell = env.get("SHELL", "")
    if not shell:
        add("SHELL", "warn", "SHELL is not set")
    elif not os.path.isabs(shell):
        add("SHELL", "warn", f"SHELL is not absolute: {shell}")
    elif not os.path.isfile(shell):
        add("SHELL", "error", f"SHELL does not exist: {shell}")
    elif not os.access(shell, os.X_OK):
        add("SHELL", "warn", f"SHELL is not executable: {shell}")
    else:
        add("SHELL", "ok", shell)

    term = env.get("TERM", "")
    if not term:
        add("TERM", "warn", "TERM is not set")
    elif term == "dumb":
        add("TERM", "warn", "TERM=dumb (no interactive terminal features)")
    else:
        add("TERM", "ok", term)

    if not (env.get("USER") or env.get("LOGNAME")):
        add("USER", "warn", "neither USER nor LOGNAME is set")
    else:
        add("USER", "ok", env.get("USER") or env.get("LOGNAME"))

    if not (env.get("LANG") or env.get("LC_ALL") or env.get("LC_CTYPE")):
        add("LANG", "warn", "no locale variable (LANG, LC_ALL, LC_CTYPE) is set")
    else:
        add("LANG", "ok", env.get("LC_ALL") or env.get("LANG") or "LC_CTYPE set")

    tmpdir = env.get("TMPDIR")
    if tmpdir:
        if not os.path.isdir(tmpdir):
            add("TMPDIR", "warn", f"TMPDIR is not a directory: {tmpdir}")
        elif not os.access(tmpdir, os.W_OK):
            add("TMPDIR", "warn", f"TMPDIR is not writable: {tmpdir}")
        else:
            add("TMPDIR", "ok", tmpdir)

    pwd = env.get("PWD")
    if pwd and os.path.isdir(pwd):
        try:
            actual = os.getcwd()
        except OSError:
            actual = None
        if actual and os.path.realpath(pwd) != os.path.realpath(actual):
            add("PWD", "warn", f"PWD ({pwd}) differs from the working directory ({actual})")
        else:
            add("PWD", "ok", pwd)

    return checks


def worst(checks):
    for level in ("error", "warn"):
        if any(c["status"] == level for c in checks):
            return level
    return "ok"


def self_test():
    import tempfile
    with tempfile.TemporaryDirectory() as home:
        clean = {
            "PATH": "/usr/bin:/bin",
            "HOME": home,
            "SHELL": "/bin/sh",
            "TERM": "xterm-256color",
            "USER": "tester",
            "LANG": "C.UTF-8",
            "TMPDIR": "/tmp",
            "PWD": os.getcwd(),
        }
        checks = audit(clean)
        assert worst(checks) == "ok", checks

        dirty = dict(clean)
        dirty["PATH"] = "/usr/bin:/bin:/usr/bin:/no/such/dir:relative"
        dirty["HOME"] = "/no/such/home"
        dirty["TERM"] = "dumb"
        dirty.pop("LANG")
        dirty["PWD"] = "/tmp"
        findings = audit(dirty)
        messages = " | ".join(c["message"] for c in findings)
        assert any(c["check"] == "HOME" and c["status"] == "error" for c in findings)
        assert "duplicate" in messages and "missing directory" in messages
        assert "relative" in messages and "TERM=dumb" in messages
        assert worst(findings) == "error"
    print("self-test OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--self-test", action="store_true", help="run offline self tests")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0

    checks = audit(dict(os.environ))
    summary = {level: sum(1 for c in checks if c["status"] == level)
               for level in ("ok", "warn", "error")}
    if args.json:
        print(json.dumps({"checks": checks, "summary": summary}, indent=2, sort_keys=True))
    else:
        for c in checks:
            print(f"{c['status'].upper():5} {c['check']:10} {c['message']}")
        print(f"\n{summary['ok']} ok, {summary['warn']} warning, {summary['error']} error")
    return 0 if worst(checks) == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
