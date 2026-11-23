# 65 - sshd-audit

Parse `sshd_config`, follow `Include` globs (relative includes resolve from the
including file's directory, as OpenSSH does), and flag weak global settings.
Directives inside `Match` blocks are tracked but deliberately not treated as
global policy.

Checks include:

- `PermitRootLogin yes` (high), forced-commands-only (medium)
- `PasswordAuthentication yes` (medium)
- `PermitEmptyPasswords yes` (critical)
- `PubkeyAuthentication no` (medium)
- `MaxAuthTries` above 6
- `X11Forwarding yes`, `HostbasedAuthentication yes`, `IgnoreRhosts no`
- legacy `Protocol 1`

First global occurrence wins, mirroring sshd's own precedence. Unset keys are
reported as informational notes with their usual defaults.

## Usage

```sh
./sshd_audit.py                          # /etc/ssh/sshd_config
./sshd_audit.py /etc/ssh/sshd_config --json
./sshd_audit.py ./testdata/sshd_config
```

JSON output contains `config`, `findings` (severity, key, value, file, line,
message), per-severity `counts`, informational `notes`, and `files_parsed`.

## Exit codes

| code | meaning |
|------|---------|
| 0 | parsed, no critical/high findings |
| 1 | at least one critical or high finding |
| 2 | config missing or unreadable |

## Self-test

```sh
./sshd_audit.py --self-test
```

Builds a temporary config with an `Include` glob, weak settings, and a `Match`
overrides, then verifies include parsing, severities, exit codes, and that the
Match-block exception is honored.
