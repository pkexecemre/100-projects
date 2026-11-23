#!/usr/bin/env python3
"""Unicode-aware slugify: transliterate to ASCII or keep Unicode letters."""

import argparse
import re
import sys
import unicodedata

TRANSLIT = {
    "\u00c6": "AE", "\u00e6": "ae", "\u00d8": "O", "\u00f8": "o",
    "\u0141": "L", "\u0142": "l", "\u0110": "D", "\u0111": "d",
    "\u00de": "TH", "\u00fe": "th", "\u00d0": "D", "\u00f0": "d",
    "\u1e9e": "SS",
}


def slugify(text, sep="-", keep_unicode=False):
    """Lowercase text and join alphanumeric runs with sep."""
    if not sep:
        raise ValueError("separator must not be empty")
    text = text.casefold()
    if keep_unicode:
        text = unicodedata.normalize("NFC", text)
    else:
        text = unicodedata.normalize("NFKD", text)
        text = "".join(TRANSLIT.get(char, char) for char in text)
        text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.replace("'", "").replace("\u2019", "")
    runs = []
    current = []
    for char in text:
        allowed = char.isalnum() and (keep_unicode or char.isascii())
        combining = keep_unicode and unicodedata.combining(char)
        if allowed:
            current.append(char)
        elif combining:
            if current:
                current.append(char)
        elif current:
            runs.append("".join(current))
            current = []
    if current:
        runs.append("".join(current))
    return sep.join(runs)


def self_test():
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("  Hello   World  ") == "hello-world"
    assert slugify("H\u00e9llo W\u00f6rld") == "hello-world"
    assert slugify("H\u00e9llo W\u00f6rld", keep_unicode=True) == "h\u00e9llo-w\u00f6rld"
    assert slugify("\u4f60\u597d \u4e16\u754c") == ""
    assert slugify("\u4f60\u597d \u4e16\u754c", keep_unicode=True) == "\u4f60\u597d-\u4e16\u754c"
    assert slugify("Stra\u00dfe") == "strasse"
    assert slugify("\u00c6ther \u00d8re") == "aether-ore"
    assert slugify("\u0130stanbul", keep_unicode=True) == "i\u0307stanbul"
    assert slugify("don't stop") == "dont-stop"
    assert slugify("a__b--c", sep="_") == "a_b_c"
    assert slugify("100% ready?", sep=".") == "100.ready"
    assert slugify("!!!", sep="-") == ""
    try:
        slugify("x", sep="")
    except ValueError:
        pass
    else:
        raise AssertionError("empty separator should fail")
    print("self-test: 12 checks passed")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Turn text into a URL-friendly slug.")
    parser.add_argument("words", nargs="*", help="text to slugify (default: stdin)")
    parser.add_argument("--sep", "--separator", dest="sep", default="-",
                        help="separator between words (default '-')")
    parser.add_argument("--keep-unicode", action="store_true",
                        help="keep non-ASCII letters instead of transliterating")
    parser.add_argument("--self-test", action="store_true",
                        help="run offline checks and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        self_test()
        return 0
    if not args.sep:
        parser.error("--sep must not be empty")

    if args.words:
        text = " ".join(args.words)
    else:
        if sys.stdin.isatty():
            parser.error("give text arguments or pipe input on stdin")
        text = sys.stdin.read()

    try:
        print(slugify(text, args.sep, args.keep_unicode))
    except ValueError as exc:
        print("slugify: error: %s" % exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
