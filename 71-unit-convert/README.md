# 71 - unit-convert

Convert between byte sizes (SI and IEC), durations, lengths and weights from
one small, explicit unit registry. No third-party packages.

## Usage

```console
$ ./unit_convert.py 1.5 GiB MB
1.5 GiB = 1610.612736 MB
$ ./unit_convert.py 90 min h
90 min = 1.5 h
$ ./unit_convert.py 5 mi km --json
{
  "value": 5.0,
  "from": "mi",
  "to": "km",
  "category": "length",
  "result": 8.04672
}
$ ./unit_convert.py --list       # full registry, grouped by category
```

Supported units:

- bytes: `B KB MB GB TB PB` (powers of 1000) and `KiB MiB GiB TiB PiB` (powers of 1024)
- duration: `ns us ms s min h d wk`
- length: `mm cm m km in ft yd mi`
- weight: `mg g kg t oz lb`

Names are matched case-insensitively (`gib` -> `GiB`). A name that exists in
more than one category is rejected as ambiguous; conversions across categories
are always rejected.

## Options

- `--list` - print the registry and exit
- `--json` - output a JSON object with `value`, `from`, `to`, `category`, `result`
- `--precision N` - significant digits for decimal output (1-17, default 12)
- `--self-test` - run built-in conversion checks

## Exit codes

- `0` success (including `--help`, `--list`, `--self-test`)
- `1` runtime error: unknown/ambiguous unit, mixed categories, bad number
- `2` usage error: missing positional arguments or invalid option value

## Self-test

```console
$ ./unit_convert.py --self-test
self-test: all checks passed
```
