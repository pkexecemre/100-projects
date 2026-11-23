#!/usr/bin/env python3
"""Draw an ASCII banner box around text, with wrapping and several styles."""
import argparse
import sys
import textwrap

STYLES = {
    "box": {"tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|"},
    "heavy": {"tl": "#", "tr": "#", "bl": "#", "br": "#", "h": "#", "v": "#"},
    "equals": {"tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "=", "v": "|"},
    "stars": {"tl": "*", "tr": "*", "bl": "*", "br": "*", "h": "*", "v": "*"},
    "slash": {"tl": "/", "tr": "\\", "bl": "\\", "br": "/", "h": "-", "v": "|"},
}


def banner(text: str, style: str = "box", width: int = 40, align: str = "left") -> str:
    if width < 8:
        raise ValueError("width must be at least 8")
    if style not in STYLES:
        raise ValueError(f"unknown style {style!r}")
    chars = STYLES[style]
    inner = width - 4
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        wrapped = textwrap.wrap(paragraph, width=inner, break_long_words=True,
                                break_on_hyphens=False) or [""]
        for line in wrapped:
            if align == "center":
                lines.append(line.center(inner))
            elif align == "right":
                lines.append(line.rjust(inner))
            else:
                lines.append(line.ljust(inner))
    top = chars["tl"] + chars["h"] * (width - 2) + chars["tr"]
    bottom = chars["bl"] + chars["h"] * (width - 2) + chars["br"]
    body = [f'{chars["v"]} {line} {chars["v"]}' for line in lines]
    return "\n".join([top, *body, bottom])


def self_test() -> None:
    for style in STYLES:
        out = banner("hello world", style=style, width=20).splitlines()
        assert len(out) >= 3
        assert all(len(row) == 20 for row in out), (style, out)
        assert out[0][0] == STYLES[style]["tl"]
    wrapped = banner("one two three four five", width=14).splitlines()
    assert len(wrapped) == 5, wrapped  # two borders and three wrapped text rows
    assert all(len(row) == 14 for row in wrapped)
    centered = banner("hi", width=12, align="center").splitlines()[1]
    assert centered == "|    hi    |"
    try:
        banner("x", width=4)
    except ValueError:
        pass
    else:
        raise AssertionError("small width was accepted")
    print(f"self-test: ok ({len(STYLES)} styles)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Wrap text in an ASCII banner box.")
    ap.add_argument("text", nargs="*", help="text to put in the banner")
    ap.add_argument("--style", default="box", help=", ".join(STYLES) + " (default: box)")
    ap.add_argument("--width", type=int, default=40, help="total banner width in columns (default: 40)")
    ap.add_argument("--align", choices=["left", "center", "right"], default="left")
    ap.add_argument("--self-test", action="store_true", help="run internal checks and exit")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.text:
        ap.error("provide at least one word of text")
    if args.style not in STYLES:
        print(f"banner: unknown style {args.style!r}; choose from {', '.join(STYLES)}", file=sys.stderr)
        return 2
    try:
        print(banner(" ".join(args.text), args.style, args.width, args.align))
    except ValueError as exc:
        print(f"banner: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
