# 100-sysfetch

A compact neofetch-style system summary with an ASCII penguin logo. It reports
the OS pretty name, kernel, architecture, hostname, CPU model and core count,
memory use, uptime, root filesystem use, and the Python version. Everything is
read from the standard library and `/proc`/`/etc/os-release` (with fallbacks),
never from the network.

## Usage

```sh
./sysfetch.py
./sysfetch.py --no-logo
./sysfetch.py --json | python3 -m json.tool
./sysfetch.py --self-test
```

`--json` emits a flat object with keys such as `os`, `kernel`, `cores`,
`memory_used`, `memory_percent`, `uptime`, `uptime_seconds`, `disk_percent`,
and `python`. Fields that cannot be determined on the current platform are
reported as `"unknown"` or `null` rather than failing.

## Exit codes

- `0` success, including `--self-test`
- `1` bad flag (argparse)
- `2` system data could not be read
