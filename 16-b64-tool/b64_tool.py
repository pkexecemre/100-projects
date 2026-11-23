#!/usr/bin/env python3
"""Encode or decode Base64 text, with optional URL-safe alphabet."""

import argparse
import base64
import binascii
import re
import sys

B64_RE = re.compile(r"^[A-Za-z0-9+/]*={0,2}$")


def encode_bytes(data, urlsafe=False, wrap=0):
    encoder = base64.urlsafe_b64encode if urlsafe else base64.b64encode
    text = encoder(data).decode("ascii")
    if wrap and wrap > 0:
        text = "\n".join(text[i:i + wrap] for i in range(0, len(text), wrap))
    return text


def decode_text(text, urlsafe=False):
    """Strictly decode Base64, tolerating URL-safe characters and missing padding."""
    compact = "".join(text.split())
    if not compact:
        return b""
    compact = compact.replace("-", "+").replace("_", "/")
    if not B64_RE.match(compact):
        raise ValueError("invalid base64 characters")
    if "=" in compact and len(compact) % 4 != 0:
        raise ValueError("invalid base64 padding")
    if len(compact) % 4 == 1:
        raise ValueError("invalid base64 length")
    compact += "=" * (-len(compact) % 4)
    try:
        return base64.b64decode(compact, validate=True)
    except binascii.Error as exc:
        raise ValueError("invalid base64 data: %s" % exc)


def self_test():
    samples = [b"hello world", b"", bytes(range(256)), "caf\u00e9".encode("utf-8")]
    for sample in samples:
        assert decode_text(encode_bytes(sample)) == sample
        assert decode_text(encode_bytes(sample, urlsafe=True), urlsafe=True) == sample
    blob = bytes([0xfb, 0xff, 0xbf])
    assert "-" in encode_bytes(blob, urlsafe=True)
    assert "+" in encode_bytes(blob)
    assert decode_text(encode_bytes(b"hi")[:-1]) == b"hi"  # missing padding
    assert decode_text("aGVs\nbG8=") == b"hello"
    assert decode_text("") == b""
    for bad in ["!!!!", "a", "ab=c", "abcde", "a===", "ab=", "aGVsbG8=="]:
        try:
            decode_text(bad)
        except ValueError:
            continue
        raise AssertionError("should reject %r" % bad)
    wrapped = encode_bytes(b"x" * 100, wrap=20)
    assert "\n" in wrapped and decode_text(wrapped) == b"x" * 100
    print("self-test: 12 checks passed")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Base64 encode or decode text, stdin, or file contents.")
    parser.add_argument("text", nargs="?", help="input text (default: stdin)")
    parser.add_argument("-d", "--decode", action="store_true",
                        help="decode instead of encode")
    parser.add_argument("--file", metavar="PATH",
                        help="read input from PATH (raw bytes when encoding)")
    parser.add_argument("--urlsafe", action="store_true",
                        help="use the URL-safe alphabet when encoding")
    parser.add_argument("--wrap", type=int, default=0, metavar="N",
                        help="wrap encoded output at N columns (default 0)")
    parser.add_argument("-o", "--output", metavar="PATH",
                        help="write output to PATH (binary when decoding)")
    parser.add_argument("--self-test", action="store_true",
                        help="run offline checks and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        self_test()
        return 0
    if args.text is not None and args.file:
        parser.error("give text or --file, not both")
    if args.wrap < 0:
        parser.error("--wrap must be >= 0")

    try:
        if args.decode:
            if args.text is not None:
                source = args.text
            elif args.file:
                with open(args.file, encoding="utf-8") as handle:
                    source = handle.read()
            else:
                source = sys.stdin.read()
            data = decode_text(source, args.urlsafe)
            if args.output:
                with open(args.output, "wb") as handle:
                    handle.write(data)
            else:
                try:
                    print(data.decode("utf-8"))
                except UnicodeDecodeError:
                    print("b64-tool: error: decoded bytes are not UTF-8; use -o FILE",
                          file=sys.stderr)
                    return 2
        else:
            if args.text is not None:
                data = args.text.encode("utf-8")
            elif args.file:
                with open(args.file, "rb") as handle:
                    data = handle.read()
            else:
                data = sys.stdin.buffer.read()
            encoded = encode_bytes(data, args.urlsafe, args.wrap)
            if args.output:
                with open(args.output, "w", encoding="ascii") as handle:
                    handle.write(encoded + "\n")
            else:
                print(encoded)
    except (OSError, ValueError) as exc:
        print("b64-tool: error: %s" % exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
