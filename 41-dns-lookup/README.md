# 41 - dns-lookup

Resolve A/AAAA records with `getaddrinfo` or do a reverse PTR lookup, with a
hard timeout so a broken resolver cannot hang the terminal. Pure Python 3
standard library.

## Usage

```sh
python3 dns_lookup.py example.com
python3 dns_lookup.py example.com --type a
python3 dns_lookup.py example.com --type aaaa --json
python3 dns_lookup.py 192.0.2.10 --reverse
python3 dns_lookup.py --self-test
```

Forward output lists one record per line (`A` or `AAAA`). `--json` emits an
object with `query`, `mode`, and `records` (or `error`). DNS work runs in a
daemon thread bounded by `--timeout`, so resolution failures return promptly.

## Exit codes

- `0` - lookup succeeded and at least one record was returned
- `1` - lookup succeeded but the name has no records of the requested type
- `2` - usage error, resolver error, timeout, or no PTR record

## Notes

Reverse lookups use `gethostbyaddr`; the aliases it returns are printed below
the canonical name. No external packages or network access are needed for
`--self-test`.
