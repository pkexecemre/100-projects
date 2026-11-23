# 72 - timestamp

Convert between Unix epoch values, ISO 8601 timestamps and relative spans.
Everything is parsed and displayed timezone-aware; naive ISO input is treated
as UTC.

## Usage

```console
$ ./timestamp.py 1700000000 --utc
input      1700000000
epoch      1700000000
iso        2023-11-14T22:13:20+00:00
utc        2023-11-14T22:13:20Z
local      2023-11-15T01:13:20+03:00
timezone   UTC
relative   3y 9d ago

$ ./timestamp.py '30m ago' --utc --json
{
  "input": "30m ago",
  "epoch": 1795469800,
  "iso": "2026-11-23T21:36:40+00:00",
  "utc": "2026-11-23T21:36:40Z",
  "local": "2026-11-24T00:36:40+03:00",
  "timezone": "UTC",
  "relative": "30m ago"
}
$ ./timestamp.py 2024-06-01T12:00:00Z --tz Europe/Berlin
$ ./timestamp.py 1700000000000      # milliseconds are auto-detected
```

`local` and `relative` depend on the host timezone and clock, so the values
above are a snapshot.

Accepted inputs:

- epoch seconds (or milliseconds when the absolute value exceeds `1e11`)
- ISO 8601 dates and datetimes (`2024-06-01`, `2024-06-01T12:00:00+02:00`, `...Z`)
- `now`
- relative spans: `90m`, `-2h`, `3d ago`, `1w`, `2mo`, `1y`
  (supported units: `s m h d w mo y` and short aliases; `mo` is 30 days,
  `y` is 365 days)

## Options

- `--utc` - show the `iso` field in UTC
- `--tz ZONE` - show the `iso` field in an IANA zone (requires `--utc` absent)
- `--json` - emit one JSON object
- `--self-test` - run deterministic built-in checks

Output keys: `input`, `epoch`, `iso`, `utc`, `local`, `timezone`, `relative`.
`iso` follows the selected zone; `utc` and `local` are always included.

## Exit codes

- `0` success
- `1` parse error, unknown timezone, out-of-range epoch
- `2` usage error (`--utc` together with `--tz`)

## Self-test

```console
$ ./timestamp.py --self-test
self-test: all checks passed
```
