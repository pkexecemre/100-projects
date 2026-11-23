# 50 - selfsigned-cert

Wrapper around `openssl req -x509` that validates the common name and subject
alternative names, generates a key and certificate, locks the key down to mode
0600, and prints the SHA-256 fingerprint.

## Usage

```sh
python3 selfsigned_cert.py
python3 selfsigned_cert.py --cn dev.local --san dev.local --san 127.0.0.1
python3 selfsigned_cert.py --cn api.test --san 'DNS:api.test,DNS:*.api.test' --days 90
python3 selfsigned_cert.py --out-dir certs --key-size 3072 --json
python3 selfsigned_cert.py --self-test
```

Outputs `cert.pem` and `key.pem` in `--out-dir` (default `.`). Existing files
are not overwritten unless `--force` is given. With no `--san`, the CN is used
as a SAN; if the CN is not a valid DNS name or IP, the tool asks for an
explicit `--san` instead of silently producing a certificate with no SAN.

SAN syntax: `DNS:name`, `IP:address`, or a bare value (IP addresses are
detected automatically). Wildcards such as `*.example.test` are accepted.
Multiple entries can be repeated with `--san` or comma-separated.

## Exit codes

- `0` - certificate and key generated
- `1` - invalid CN/SAN or refusing to overwrite existing files
- `2` - openssl missing, failed, timed out, or could not write output

## Notes

The certificate is self-signed and suitable for development, internal services,
and testing. `--self-test` validates the argument logic and, when openssl is
installed, generates a throwaway certificate in a temporary directory.
