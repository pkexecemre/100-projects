# 74 - color-convert

Convert colors between hexadecimal, `rgb()` and `hsl()`. Parsing is strict by
default; `--clamp` opts into clipping out-of-range components.

## Usage

```console
$ ./color_convert.py '#336699'
hex #336699
rgb rgb(51, 102, 153)
hsl hsl(210, 50%, 40%)

$ ./color_convert.py 'hsl(0, 100%, 50%)' --json
{
  "hex": "#ff0000",
  "rgb": [
    255,
    0,
    0
  ],
  "hsl": [
    0,
    100,
    50
  ]
}
$ ./color_convert.py '#0f8' --json
$ ./color_convert.py 'rgb(300, 0, 0)' --clamp
$ ./color_convert.py '300, 0, 0' --clamp
```

Accepted inputs:

- `#rgb` / `#rrggbb` (the `#` may be omitted for six-digit hex)
- `rgb(r, g, b)` with integers 0-255, or a bare comma/space triple of integers
- `hsl(h, s%, l%)` with optional `%` signs and optional `deg` on the hue;
  hue wraps modulo 360, saturation and lightness must be 0-100

Out-of-range values fail with exit `1` unless `--clamp` is given. Percentage
RGB components and alpha channels are rejected.

## Options

- `--clamp` - clamp RGB channels to 0-255 and HSL saturation/lightness to 0-100
- `--json` - object with `hex`, `rgb` (3 ints), `hsl` (3 numbers, 0.1 precision)
- `--self-test` - known-value and round-trip checks

## Exit codes

- `0` success
- `1` unrecognized syntax, wrong component count, out-of-range value without `--clamp`
- `2` usage error (missing color argument)

## Self-test

```console
$ ./color_convert.py --self-test
self-test: all checks passed
```
