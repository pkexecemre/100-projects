# 10-url-check

Check one or more HTTP/HTTPS URLs with the standard library. For each URL it
reports the final status, how many redirects were followed, and total elapsed
time. Each request has its own timeout, and DNS failures, refused connections,
timeouts, malformed URLs and HTTP error statuses are reported as rows instead of
tracebacks.

## Usage

```sh
./url_check.py https://example.com
./url_check.py https://example.com http://127.0.0.1:8080/health --timeout 5
./url_check.py https://example.com --json
```

Connections are made directly: environment proxy variables are ignored so the
result reflects the URL itself. `2xx` and `3xx` responses count as success;
`4xx`, `5xx`, connection errors and timeouts count as failures. Redirect chains
are capped by urllib's default limit (10). `--json` emits a `results` list with
`url`, `status`, `ok`, `redirects`, `ms`, `final_url` and `note` per URL.

## Exit codes

| code | meaning |
|------|---------|
| 0 | every URL returned a 2xx or 3xx status |
| 1 | at least one URL failed, errored or used a non-HTTP scheme |
| 2 | invalid arguments (for example a non-positive timeout) |

## Test

`./url_check.py --self-test` starts a local HTTP server on an ephemeral port,
checks a direct 200, a 302 chain, a 404, an unsupported `file://` URL and a
connection to a closed loopback port. It needs no external network and shuts the
server down afterwards.
