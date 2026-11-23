# 66 - firewall-summary

One screen of local firewall state, covering four common Linux backends:

- **firewalld** - `firewall-cmd --state` / `--list-all`
- **ufw** - `ufw status verbose`
- **nftables** - `nft list ruleset`
- **iptables/ip6tables** - `-S` policy and rule counts

Each backend is classified as `active`, `inactive`, `not installed`,
`unknown (needs root)`, or `error`. Permission failures are never guessed at or
silently shown as an empty ruleset: if the kernel/daemon refuses the query, the
status says so. Commands run with `LC_ALL=C`, a per-command timeout, and no
shell.

## Usage

```sh
./firewall_summary.py
./firewall_summary.py --json
./firewall_summary.py --timeout 2
```

Text output is a four-column status table. JSON:

```json
{"root": false,
 "backends": {"ufw": {"status": "unknown (needs root)", "detail": "..."},
              "nft": {"status": "active", "detail": "2 table(s), 4 chain(s), ..."}}}
```

## Exit codes

| code | meaning |
|------|---------|
| 0 | report produced (even when backends are missing or locked down) |

The tool is read-only and never invokes a command that changes firewall state.

## Self-test

```sh
./firewall_summary.py --self-test
```

Creates fake `firewall-cmd`, `ufw`, `nft`, and `iptables` executables in a
temporary `PATH`, asserts all four parse as active with key values intact, then
runs with no tools available and asserts every backend reports
`not installed`.
