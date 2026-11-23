# 43 - http-headers

Request a URL with `urllib`, then print the final status line, the redirect
chain, and every response header. Uses a HEAD request by default and retries
with GET when a server answers HEAD with 405 or 501.

## Usage

```sh
python3 http_headers.py example.com
python3 http_headers.py https://example.com/ --method GET
python3 http_headers.py http://example.com/ --json
python3 http_headers.py https://self-signed.test/ --insecure
python3 http_headers.py --self-test
```

A missing scheme is filled in as `https://`. Redirects are followed by urllib
(limit `--max-redirects`, default 10) and each hop is recorded with its status,
source URL, and target. All network operations are bounded by `--timeout`
(default 10s). `-k/--insecure` disables certificate verification only for this
request.

## Exit codes

- `0` - response received with a 2xx/3xx status
- `1` - server replied with an HTTP error status (headers are still printed)
- `2` - bad URL or flag, DNS failure, connection failure, TLS failure, timeout
