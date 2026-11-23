# 73 - base-convert

Convert integers between binary, octal, decimal and hexadecimal with strict
prefix handling and per-base digit validation. Outputs keep the familiar
`0b` / `0o` / `0x` prefixes.

## Usage

```console
$ ./base_convert.py 0xff
dec  255
bin  0b11111111
oct  0o377
hex  0xff

$ ./base_convert.py 42 --to bin
0b101010
$ ./base_convert.py -0b1010 --json
{
  "input": "-0b1010",
  "decimal": -10,
  "bin": "-0b1010",
  "oct": "-0o12",
  "hex": "-0xa"
}
```

Input rules:

- prefixes are case-insensitive: `0b1010`, `0O17`, `0XFF`
- bare numbers are decimal (`42`, `+7`, `0`)
- an optional leading `-` or `+` is accepted before the prefix
- `_` digit separators are ignored (`1_000`); everything else must be a valid
  digit for the chosen base, otherwise the tool exits `1`

`--to {bin,oct,dec,hex}` prints only the converted value (with prefix except
for decimal). Without `--to`, all four forms are printed.

## Options

- `--to BASE` - output a single representation
- `--json` - object with `input`, `decimal`, `bin`, `oct`, `hex`
- `--self-test` - run validation and round-trip checks

## Exit codes

- `0` success
- `1` invalid digit, empty value, missing digits after a prefix
- `2` usage error (unknown `--to` value, missing argument)

## Self-test

```console
$ ./base_convert.py --self-test
self-test: all checks passed
```
