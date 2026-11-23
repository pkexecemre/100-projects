#!/usr/bin/env python3
"""Render A-Z, 0-9 and spaces as 5x7 block letters.

Usage: ./blocktext.py HELLO [SECOND-LINE ...]
Reads stdin (one line per row) when no arguments are given and stdin is piped.
"""
import argparse
import sys

FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}


def render_line(text: str) -> list[str]:
    """Return the seven output rows for one line of text."""
    chars = []
    for ch in text.upper():
        if ch not in FONT:
            raise ValueError(f"unsupported character: {ch!r} (allowed: A-Z, 0-9, space)")
        chars.append(FONT[ch])
    if not chars:
        chars = [FONT[" "]]
    rows = []
    for row in range(7):
        rows.append(" ".join(glyph[row] for glyph in chars).replace("1", "#").replace("0", " "))
    return rows


def render_text(lines: list[str]) -> str:
    blocks = ["\n".join(render_line(line)) for line in lines]
    return "\n\n".join(blocks)


def self_test() -> None:
    assert len(FONT) == 37, len(FONT)
    for ch, glyph in FONT.items():
        assert len(glyph) == 7, ch
        assert all(len(row) == 5 and set(row) <= {"0", "1"} for row in glyph), ch
    rows = render_line("A1")
    assert len(rows) == 7 and all(len(row) == 11 for row in rows)
    assert "#" in rows[0] and rows[0].count("#") >= 4
    assert len(render_text(["AB", "CD"]).splitlines()) == 15
    assert render_text([" "]).strip() == ""
    try:
        render_line("A?")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown character was accepted")
    print(f"self-test: ok ({len(FONT)} glyphs, 5x7)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Render text as 5x7 block letters.")
    ap.add_argument("lines", nargs="*", help="one argument per output line; stdin is read if piped")
    ap.add_argument("--self-test", action="store_true", help="run internal checks and exit")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    lines = args.lines
    if not lines:
        if sys.stdin.isatty():
            ap.error("provide at least one line of text (or pipe stdin)")
        lines = [line for line in sys.stdin.read().splitlines() if line.strip()]
    if not lines:
        ap.error("no non-empty input lines")
    try:
        print(render_text(lines))
    except ValueError as exc:
        print(f"blocktext: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
