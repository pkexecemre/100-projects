# 79 - roman

Convert integers to Roman numerals and Roman numerals back to integers, with
strict canonical validation and range checks (1-3999).

## Usage

```console
$ ./roman.py 1994
value 1994
roman MCMXCIV
$ ./roman.py MCMXCIV
value 1994
roman MCMXCIV
$ ./roman.py 42 --json
{
  "input": "42",
  "value": 42,
  "roman": "XLII"
}
```

The converter uses the standard subtractive set (`IV IX XL XC CD CM`) and
accepts lowercase input (`mcmxciv`). Validation is strict: only canonical
forms are allowed, so `IIII`, `IC`, `VX`, `CMCM` and `MMMM` all exit `1`.

## Options

- `--json` - object with `input`, `value` and `roman`
- `--self-test` - round-trip checks for known numerals plus invalid cases

## Exit codes

- `0` success
- `1` out-of-range number, malformed or non-canonical Roman numeral, empty input
- `2` usage error (missing argument)

## Self-test

```console
$ ./roman.py --self-test
self-test: all checks passed
```
