#!/usr/bin/env python3
"""selfsigned-cert: create a self-signed certificate and key with SANs."""

import argparse
import ipaddress
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile

CN_RE = re.compile(r"^[A-Za-z0-9 ._-]+$")
LABEL_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")
FINGERPRINT_RE = re.compile(r"^(?:[0-9A-F]{2}:){31}[0-9A-F]{2}$")


class OpenSSLError(RuntimeError):
    pass


def validate_cn(value):
    cn = value.strip()
    if not cn or len(cn) > 64:
        raise ValueError("CN must be 1-64 characters")
    if not CN_RE.match(cn):
        raise ValueError("CN may contain letters, digits, spaces, dot, dash, underscore")
    if cn.startswith("-"):
        raise ValueError("CN cannot start with a dash")
    return cn


def validate_dns(name):
    candidate = name[:-1] if name.endswith(".") else name
    if candidate.startswith("*."):
        candidate = candidate[2:]
    if not candidate or len(candidate) > 253:
        raise ValueError("invalid DNS name %r" % name)
    if any(not LABEL_RE.match(label) for label in candidate.split(".")):
        raise ValueError("invalid DNS name %r" % name)
    return name


def parse_san(value):
    item = value.strip()
    if not item:
        raise ValueError("empty SAN")
    lowered = item.lower()
    if lowered.startswith("dns:"):
        return "DNS:" + validate_dns(item[4:].strip())
    if lowered.startswith("ip:"):
        try:
            return "IP:" + str(ipaddress.ip_address(item[3:].strip()))
        except ValueError:
            raise ValueError("invalid IP SAN %r" % item)
    try:
        return "IP:" + str(ipaddress.ip_address(item))
    except ValueError:
        return "DNS:" + validate_dns(item)


def build_sans(cn, extras):
    if not extras:
        try:
            return [parse_san(cn)]
        except ValueError:
            raise ValueError("CN %r is not a valid DNS/IP SAN; pass --san" % cn)
    result = []
    seen = set()
    for raw in extras:
        for part in raw.split(","):
            if not part.strip():
                continue
            san = parse_san(part)
            key = san.lower()
            if key not in seen:
                seen.add(key)
                result.append(san)
    if not result:
        raise ValueError("no SANs given")
    return result


def openssl(*args, timeout=120):
    try:
        proc = subprocess.run(["openssl", *args], capture_output=True, text=True,
                              timeout=timeout)
    except FileNotFoundError:
        raise OpenSSLError("openssl executable not found")
    except subprocess.TimeoutExpired:
        raise OpenSSLError("openssl timed out")
    if proc.returncode != 0:
        lines = (proc.stderr or proc.stdout).strip().splitlines()
        raise OpenSSLError(lines[-1] if lines else "openssl failed")
    return proc.stdout


def inspect(cert_path):
    def field(*args):
        output = openssl("x509", "-in", cert_path, "-noout", *args).strip()
        return output.split("=", 1)[-1].strip()

    return {
        "subject": field("-subject"),
        "not_after": field("-enddate"),
        "sha256": field("-fingerprint", "-sha256"),
    }


def generate(cert_path, key_path, cn, sans, days, key_size):
    try:
        openssl("req", "-x509", "-newkey", "rsa:%d" % key_size, "-sha256",
                "-nodes", "-days", str(days), "-keyout", key_path,
                "-out", cert_path, "-subj", "/CN=%s" % cn,
                "-addext", "subjectAltName=%s" % ",".join(sans))
        os.chmod(key_path, stat.S_IRUSR | stat.S_IWUSR)
        info = inspect(cert_path)
    except OpenSSLError:
        for path in (cert_path, key_path):
            try:
                os.unlink(path)
            except OSError:
                pass
        raise
    if not FINGERPRINT_RE.match(info["sha256"]):
        raise OpenSSLError("could not read certificate fingerprint")
    return info


def positive_int(text):
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def self_test():
    assert validate_cn("localhost") == "localhost"
    assert validate_cn("Example Test") == "Example Test"
    for bad in ("", "bad/name", "x=y", "-leading", "a\nb", "x" * 65):
        try:
            validate_cn(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("accepted bad CN %r" % bad)
    assert parse_san("example.test") == "DNS:example.test"
    assert parse_san("*.example.test") == "DNS:*.example.test"
    assert parse_san("IP:192.0.2.1") == "IP:192.0.2.1"
    assert parse_san("2001:db8::1") == "IP:2001:db8::1"
    for bad in ("bad/name", "IP:999.1.1.1", ""):
        try:
            parse_san(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("accepted bad SAN %r" % bad)
    assert build_sans("localhost", None) == ["DNS:localhost"]
    assert build_sans("localhost", ["example.test,IP:127.0.0.1"]) == [
        "DNS:example.test", "IP:127.0.0.1"]
    try:
        build_sans("bad name", None)
    except ValueError:
        pass
    else:
        raise AssertionError("accepted CN with no usable SAN")

    if not shutil.which("openssl"):
        print("self-test: ok (validation only; openssl not installed)")
        return 0
    with tempfile.TemporaryDirectory() as directory:
        cert_path = os.path.join(directory, "cert.pem")
        key_path = os.path.join(directory, "key.pem")
        info = generate(cert_path, key_path, "localhost",
                        ["DNS:localhost", "IP:127.0.0.1"], 1, 2048)
        assert os.path.getsize(cert_path) > 0 and os.path.getsize(key_path) > 0
        assert FINGERPRINT_RE.match(info["sha256"]), info["sha256"]
        assert "localhost" in info["subject"], info["subject"]
        mode = stat.S_IMODE(os.stat(key_path).st_mode)
        assert mode == 0o600, oct(mode)
    print("self-test: ok (validation, SAN building, end-to-end generation)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generate a self-signed TLS certificate.")
    ap.add_argument("--cn", default="localhost", help="common name (default: localhost)")
    ap.add_argument("--san", action="append",
                    help="SAN entry, repeatable (DNS:..., IP:..., or bare name)")
    ap.add_argument("--days", type=positive_int, default=365, help="validity (default: 365)")
    ap.add_argument("--key-size", type=int, choices=(2048, 3072, 4096), default=2048,
                    help="RSA key size (default: 2048)")
    ap.add_argument("--out-dir", default=".", help="output directory (default: .)")
    ap.add_argument("--force", action="store_true", help="overwrite cert.pem/key.pem")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--self-test", action="store_true", help="run offline checks")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    try:
        cn = validate_cn(args.cn)
        sans = build_sans(cn, args.san)
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1

    out_dir = os.path.abspath(os.path.expanduser(args.out_dir))
    cert_path = os.path.join(out_dir, "cert.pem")
    key_path = os.path.join(out_dir, "key.pem")
    existing = [path for path in (cert_path, key_path) if os.path.exists(path)]
    if existing and not args.force:
        print("error: refusing to overwrite %s (use --force)" % ", ".join(existing),
              file=sys.stderr)
        return 1
    try:
        os.makedirs(out_dir, exist_ok=True)
        info = generate(cert_path, key_path, cn, sans, args.days, args.key_size)
    except OpenSSLError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    except OSError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2

    result = {"cert": cert_path, "key": key_path, "common_name": cn,
              "sans": sans, **info}
    if args.json:
        print(json.dumps(result))
    else:
        print("certificate: %s" % cert_path)
        print("key:         %s" % key_path)
        print("subject:     %s" % info["subject"])
        print("sans:        %s" % ", ".join(sans))
        print("not_after:   %s" % info["not_after"])
        print("sha256:      %s" % info["sha256"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
