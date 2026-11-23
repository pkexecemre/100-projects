# 70 - secret-scan

Scan files for common credential shapes and print every hit with the secret
redacted (first four and last four characters, middle starred). Raw matches are
never written to output.

Detected patterns:

| name | example shape |
|------|---------------|
| `aws_access_key` | `AKIA` + 16 uppercase alphanumerics |
| `aws_secret_key` | `aws_secret_access_key = <40 chars>` |
| `private_key` | `-----BEGIN ... PRIVATE KEY-----` headers |
| `github_token` | `ghp_...`, `github_pat_...` |
| `slack_token` | `xoxb-...`, `xoxp-...`, etc. |
| `openai_key` | `sk-...` |
| `jwt` | three base64url segments starting `eyJ` |
| `generic_secret` | `api_key`/`secret`/`token`/`password` assigned a quoted 16+ char value |

Binary files (NUL in the first 8 KiB), files above `--max-size` (default
2 MB), `.git`, `node_modules`, virtualenvs, build output, and common binary
extensions are skipped. Symlinks are not followed.

## Usage

```sh
./secret_scan.py .                       # text output
./secret_scan.py --json ~/src ~/configs
./secret_scan.py --max-size 500000 --exclude vendor .
```

JSON output contains `scanned_files`, `count`, per-pattern `counts`, and
`findings` with `file`, `line`, `pattern`, redacted `match`, and `length`.

## Exit codes

| code | meaning |
|------|---------|
| 0 | scan completed, no findings |
| 1 | at least one finding |
| 2 | a supplied path does not exist |

## Self-test

```sh
./secret_scan.py --self-test
```

Writes a fake AWS key and a private-key header into a temporary tree, then
asserts both are detected, the full key never appears in output, redaction has
the expected shape, a clean tree exits 0, and a missing path exits 2. All test
credentials are synthetic.
