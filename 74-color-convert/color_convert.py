#!/usr/bin/env python3
"""Convert colors between hex, rgb() and hsl() with strict validation."""

import argparse
import colorsys
import json
import re
import sys


def fmt_number(value):
    value = round(value, 1)
    if value == int(value):
        return str(int(value))
    return f"{value:g}"


def bounded(value, low, high, label, clamp):
    if value < low or value > high:
        if clamp:
            return min(max(value, low), high)
        raise ValueError(f"{label} {value:g} outside {low}-{high} (use --clamp)")
    return value


def split_parts(inner):
    parts = [p for p in re.split(r"[\s,]+", inner.strip()) if p]
    if not parts:
        raise ValueError("empty component list")
    return parts


def parse_color(text, clamp=False):
    raw = text.strip().lower()
    if not raw:
        raise ValueError("empty color")
    hex_text = raw[1:] if raw.startswith("#") else raw
    if re.fullmatch(r"(?:[0-9a-f]{3}|[0-9a-f]{6})", hex_text) and (
            raw.startswith("#") or not raw.startswith("rgb") and not raw.startswith("hsl")):
        if len(hex_text) == 3:
            hex_text = "".join(ch * 2 for ch in hex_text)
        rgb = tuple(int(hex_text[i:i + 2], 16) for i in (0, 2, 4))
        return rgb, rgb_to_hsl(*rgb)

    match = re.fullmatch(r"rgb\(\s*([^)]*)\)", raw)
    if match:
        parts = split_parts(match.group(1))
        if len(parts) != 3:
            raise ValueError("rgb() needs exactly 3 components")
        if any("%" in p for p in parts):
            raise ValueError("percentage RGB components are not supported")
        channels = []
        for index, part in enumerate(parts):
            if not re.fullmatch(r"[+-]?\d+", part):
                raise ValueError(f"rgb component {index + 1} is not an integer: {part!r}")
            channels.append(bounded(int(part), 0, 255, f"channel {index + 1}", clamp))
        rgb = tuple(channels)
        return rgb, rgb_to_hsl(*rgb)

    match = re.fullmatch(r"hsl\(\s*([^)]*)\)", raw)
    if match:
        parts = split_parts(match.group(1))
        if len(parts) != 3:
            raise ValueError("hsl() needs exactly 3 components")
        try:
            hue = float(re.sub(r"deg$", "", parts[0]))
            sat = float(parts[1].rstrip("%"))
            light = float(parts[2].rstrip("%"))
        except ValueError:
            raise ValueError("hsl components must be numbers")
        if not all(map(lambda v: v == v and abs(v) != float("inf"), (hue, sat, light))):
            raise ValueError("hsl components must be finite")
        hue %= 360.0
        sat = bounded(sat, 0, 100, "saturation", clamp)
        light = bounded(light, 0, 100, "lightness", clamp)
        return hsl_to_rgb(hue, sat, light), (hue, sat, light)

    parts = [p for p in re.split(r"[\s,]+", raw) if p]
    if len(parts) == 3 and all(re.fullmatch(r"[+-]?\d+", p) for p in parts):
        channels = [bounded(int(p), 0, 255, f"channel {i + 1}", clamp)
                    for i, p in enumerate(parts)]
        rgb = tuple(channels)
        return rgb, rgb_to_hsl(*rgb)

    raise ValueError(
        f"unrecognized color {text!r}; use #rrggbb, #rgb, rgb(r,g,b), or hsl(h,s%,l%)"
    )


def rgb_to_hsl(red, green, blue):
    hue, light, sat = colorsys.rgb_to_hls(red / 255.0, green / 255.0, blue / 255.0)
    return (hue * 360.0) % 360.0, sat * 100.0, light * 100.0


def hsl_to_rgb(hue, sat, light):
    red, green, blue = colorsys.hls_to_rgb((hue % 360.0) / 360.0, light / 100.0, sat / 100.0)
    return tuple(int(round(channel * 255)) for channel in (red, green, blue))


def hex_text(rgb):
    return "#" + "".join(f"{channel:02x}" for channel in rgb)


def self_test():
    rgb, hsl = parse_color("#ff0000")
    assert rgb == (255, 0, 0)
    assert tuple(round(v, 1) for v in hsl) == (0.0, 100.0, 50.0)
    assert hex_text(parse_color("#0f8")[0]) == "#00ff88"
    assert hex_text(parse_color("rgb(51, 102, 153)")[0]) == "#336699"
    assert hex_text(parse_color("hsl(210, 50%, 40%)")[0]) == "#336699"
    assert hex_text(parse_color("hsl(210, 50, 40)")[0]) == "#336699"
    assert hex_text(parse_color("300,0,0", clamp=True)[0]) == "#ff0000"
    assert hex_text(parse_color("hsl(400, 50%, 50%)")[0]) == hex_text(
        parse_color("hsl(40, 50%, 50%)")[0])
    assert [round(v, 1) for v in parse_color("#336699")[1]] == [210.0, 50.0, 40.0]
    for bad in ("", "#12", "rgb(1,2)", "rgb(1,2,300)", "hsl(0,101%,50%)", "nope"):
        try:
            parse_color(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted invalid color {bad!r}")
    print("self-test: all checks passed")


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--self-test" in argv:
        self_test()
        return 0

    ap = argparse.ArgumentParser(
        description="Convert colors between hex, rgb() and hsl().",
        epilog="Examples: color_convert.py '#336699' | color_convert.py 'hsl(0,100%,50%)'",
    )
    ap.add_argument("color", help="#rgb, #rrggbb, rgb(r,g,b), or hsl(h,s%%,l%%)")
    ap.add_argument("--clamp", action="store_true",
                    help="clamp out-of-range RGB/HSL components instead of failing")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    try:
        rgb, hsl = parse_color(args.color, args.clamp)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    h, s, l = (round(v, 1) for v in hsl)
    payload = {
        "hex": hex_text(rgb),
        "rgb": list(rgb),
        "hsl": [h, s, l],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"hex {payload['hex']}")
        print(f"rgb rgb({rgb[0]}, {rgb[1]}, {rgb[2]})")
        print(f"hsl hsl({fmt_number(h)}, {fmt_number(s)}%, {fmt_number(l)}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
