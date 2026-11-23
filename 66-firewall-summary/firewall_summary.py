#!/usr/bin/env python3
"""Summarize local firewall state from firewalld, ufw, nft, and iptables."""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

ROOT_NEEDED = re.compile(
    r"permission denied|operation not permitted|must be root|need to be root|"
    r"requires root|are you root|you need to be root", re.I)


def run_cmd(cmd, timeout):
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, env={**os.environ, "LC_ALL": "C"})
    except FileNotFoundError:
        return None, "", "not found"
    except subprocess.TimeoutExpired:
        return None, "", "timed out"
    except OSError as exc:
        return None, "", str(exc)
    return proc.returncode, proc.stdout, proc.stderr


def backend(name, commands, parser, timeout):
    binary = commands[0][0]
    if not shutil.which(binary):
        return {"status": "not installed", "detail": "%s not in PATH" % binary}
    outputs = []
    for idx, cmd in enumerate(commands):
        code, out, err = run_cmd(cmd, timeout)
        if code is None:
            if idx > 0 and err == "not found":
                continue
            return {"status": "error", "detail": err}
        if code != 0:
            text = (err or out).strip()
            if ROOT_NEEDED.search(text):
                return {"status": "unknown (needs root)",
                        "detail": text.splitlines()[0] if text else "permission denied"}
            if re.search(r"not running|inactive|disabled", text, re.I):
                return {"status": "inactive", "detail": text.splitlines()[0]}
            return {"status": "error", "detail": text.splitlines()[0] if text else
                    "exit %d" % code}
        outputs.append((cmd, out))
    try:
        return parser(outputs)
    except (ValueError, IndexError) as exc:
        return {"status": "error", "detail": "parse failure: %s" % exc}


def parse_firewalld(outputs):
    out = outputs[-1][1]
    zone = "?"
    interfaces = services = ports = rich = 0
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("interfaces:"):
            interfaces = len([x for x in line.split(":", 1)[1].split() if x])
        elif line.startswith("services:"):
            services = len([x for x in line.split(":", 1)[1].split() if x])
        elif line.startswith("ports:"):
            ports = len([x for x in line.split(":", 1)[1].split() if x])
        elif line.startswith("rich rules:"):
            rich = len([x for x in line.split(":", 1)[1].split() if x])
    first = out.splitlines()[0].split() if out.splitlines() else []
    if first:
        zone = first[0].split("(")[0] or "?"
    return {"status": "active",
            "detail": "zone %s: %d interface(s), %d service(s), %d port(s), "
                      "%d rich rule(s)" % (zone, interfaces, services, ports, rich)}


def parse_ufw(outputs):
    out = outputs[-1][1]
    status = "inactive"
    default = "?"
    rules = 0
    for line in out.splitlines():
        low = line.lower()
        if low.startswith("status:"):
            status = "active" if "active" in low else "inactive"
        elif low.startswith("default:"):
            default = line.split(":", 1)[1].strip()
        elif line.strip() and not low.startswith(("to ", "--", "logging", "new profiles")):
            if re.match(r"^\S", line) and not line.startswith(" "):
                rules += 1
    if status == "inactive":
        return {"status": "inactive", "detail": "ufw reports inactive"}
    return {"status": "active",
            "detail": "default: %s; %d rule(s)" % (default, rules)}


def parse_nft(outputs):
    out = outputs[-1][1]
    tables = len(re.findall(r"^\s*table\s", out, re.M))
    chains = len(re.findall(r"^\s*chain\s", out, re.M))
    rules = 0
    input_policy = "?"
    for line in out.splitlines():
        low = line.lower()
        if "hook input" in low:
            match = re.search(r"policy\s+(\w+)", low)
            if match:
                input_policy = match.group(1)
        if re.search(r"\b(accept|drop|reject|return|jump|goto|masquerade)\b", low):
            if not low.strip().startswith(("chain ", "table ", "type ")):
                rules += 1
    return {"status": "active" if (tables or chains) else "inactive",
            "detail": "%d table(s), %d chain(s), ~%d rule(s), input policy %s" %
                      (tables, chains, rules, input_policy)}


def parse_iptables(outputs):
    total = 0
    policies = []
    for cmd, out in outputs:
        total += len(re.findall(r"^-A\s", out, re.M))
        for line in out.splitlines():
            if line.startswith("-P "):
                policies.append(line.strip())
    return {"status": "active" if total or policies else "inactive",
            "detail": "%d rule(s); %s" %
                      (total, "; ".join(policies) if policies else "no policy lines")}


def collect(timeout):
    backends = {
        "firewalld": backend("firewalld",
                             [["firewall-cmd", "--state"],
                              ["firewall-cmd", "--list-all"]],
                             parse_firewalld, timeout),
        "ufw": backend("ufw", [["ufw", "status", "verbose"]],
                       parse_ufw, timeout),
        "nft": backend("nft", [["nft", "list", "ruleset"]],
                       parse_nft, timeout),
        "iptables": backend("iptables",
                            [["iptables", "-S"], ["ip6tables", "-S"]],
                            parse_iptables, timeout),
    }
    return {"root": os.geteuid() == 0, "backends": backends}


def self_test():
    import subprocess
    import tempfile

    script = os.path.abspath(__file__)
    with tempfile.TemporaryDirectory() as tmp:
        bin_dir = os.path.join(tmp, "bin")
        os.makedirs(bin_dir)
        scripts = {
            "firewall-cmd": "#!/bin/sh\nif [ \"$1\" = \"--state\" ]; then echo running; "
                            "else echo \"public (active)\"; echo \"  interfaces: eth0\"; "
                            "echo \"  services: ssh dhcpv6-client\"; fi\n",
            "ufw": "#!/bin/sh\necho \"Status: active\"\n"
                   "echo \"Default: deny (incoming), allow (outgoing), disabled (routed)\"\n"
                   "echo \"22/tcp ALLOW Anywhere\"\n",
            "nft": "#!/bin/sh\necho \"table inet filter {\"\n"
                   "echo \"\tchain input {\"\n"
                   "echo \"\t\ttype filter hook input priority filter; policy drop;\"\n"
                   "echo \"\t\tct state established accept\"\n"
                   "echo \"\t}\"\n"
                   "echo \"}\"\n",
            "iptables": "#!/bin/sh\necho \"-P INPUT DROP\"\n"
                        "echo \"-A INPUT -p tcp --dport 22 -j ACCEPT\"\n",
        }
        for name, body in scripts.items():
            path = os.path.join(bin_dir, name)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(body)
            os.chmod(path, 0o755)
        env = dict(os.environ)
        env["PATH"] = bin_dir
        result = subprocess.run([sys.executable, script, "--json"],
                                capture_output=True, text=True, env=env)
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        states = {name: row["status"] for name, row in report["backends"].items()}
        assert all(state == "active" for state in states.values()), states
        assert "deny (incoming)" in report["backends"]["ufw"]["detail"]
        assert "policy drop" in report["backends"]["nft"]["detail"]
        assert "INPUT DROP" in report["backends"]["iptables"]["detail"]

        env["PATH"] = os.path.join(tmp, "empty")
        result = subprocess.run([sys.executable, script, "--json"],
                                capture_output=True, text=True, env=env)
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert all(row["status"] == "not installed"
                   for row in report["backends"].values())
    print("self-test: PASS")


def main():
    ap = argparse.ArgumentParser(
        description="Summarize firewalld, ufw, nft, and iptables state.")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--timeout", type=float, default=5.0, help="seconds per command")
    ap.add_argument("--self-test", action="store_true", help="run built-in smoke test")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    report = collect(args.timeout)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("firewall summary (euid 0: %s)" % ("yes" if report["root"] else "no"))
        for name, row in report["backends"].items():
            print("%-10s %-20s %s" % (name, row["status"], row["detail"]))
        if not report["root"]:
            print("\nnote: some backends cannot be queried without root; "
                  "'unknown (needs root)' is reported instead of guessing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
