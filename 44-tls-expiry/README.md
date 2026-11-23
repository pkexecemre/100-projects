# 44 - tls-expiry

Open a TLS connection, read the peer certificate, and report its subject,
issuer, validity window, remaining days, and DNS SANs. Exits non-zero when the
certificate is inside the warning window or already expired, which makes it
usable from cron and monitoring scripts.

## Usage

```sh
python3 tls_expiry.py example.com
python3 tls_expiry.py example.com --port 8443 --warn-days 14
python3 tls_expiry.py 192.0.2.10 --servername example.com --insecure
python3 tls_expiry.py example.com --json
python3 tls_expiry.py --self-test
```

By default the certificate chain and hostname are verified; use `--insecure`
for internal or self-signed endpoints. `--servername` overrides SNI (useful
when connecting to an IP address). The handshake is bounded by `--timeout`.

## Output

Text mode prints `host`, `subject`, `issuer`, `not_before`, `not_after`,
`days_left`, `status`, TLS version/cipher, and DNS SANs. JSON mode emits the
same fields. `status` is `OK`, `WARNING`, `EXPIRED`, or `UNKNOWN`.

## Exit codes

- `0` - certificate valid and more than `--warn-days` remain
- `1` - certificate expires within `--warn-days`, or has expired
- `2` - connection/TLS/decoding error, bad flag, or bad host
