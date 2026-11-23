# 46 - whois-lite

Query a WHOIS server over plain TCP port 43 and print the raw response.
Defaults to `whois.iana.org`, which is the right starting point for finding
the authoritative server for a TLD or IP block.

## Usage

```sh
python3 whois_lite.py example.com
python3 whois_lite.py example.com --follow
python3 whois_lite.py 192.0.2.1 --server whois.arin.net
python3 whois_lite.py example.com --json
python3 whois_lite.py --self-test
```

`--json` returns the raw text plus a `fields` map built by lowercasing keys and
grouping repeated keys into lists (WHOIS responses often repeat `status`,
`nameserver`, and `created`). `--follow` performs one additional query when
the first response contains a `refer:` or `whois:` server. The connection and
every read use `--timeout` (default 10s), and responses are capped at 2 MB.

## Exit codes

- `0` - response received and printed
- `2` - invalid query/server/flag, DNS failure, connection failure, timeout,
  or oversized response

## Notes

Queries are restricted to hostname/IP-shaped strings, which prevents injection
of extra protocol lines. The parser is exercised offline by `--self-test`.
