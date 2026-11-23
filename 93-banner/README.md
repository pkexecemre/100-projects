# 93-banner

Draw a rectangular ASCII banner around arbitrary text. Long text wraps to fit
the requested total width, and five border styles are available: `box`,
`heavy`, `equals`, `stars` and `slash`.

## Usage

```sh
./banner.py Hello world
./banner.py --style heavy --width 30 "Build complete"
./banner.py --style stars --align center --width 28 "Ship it"
./banner.py --self-test
```

Width is the total outer width including borders, so the text area is
`width - 4` columns (two border columns and two padding spaces). The minimum
width is 8. Alignment applies to each wrapped line.

## Exit codes

- `0` success, including `--self-test`
- `2` unknown style, width below 8, or other invalid input
