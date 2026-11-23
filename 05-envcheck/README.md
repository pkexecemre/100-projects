# 05-envcheck

Sanity-check the shell environment. Examines `PATH` for empty, relative,
duplicate, missing, non-directory and non-searchable entries; checks that `HOME`
exists and is writable; checks `SHELL` exists and is executable; checks `TERM`
is set and not `dumb`; and reports on `USER`/`LOGNAME`, locale variables,
`TMPDIR`, and `PWD` consistency.

## Usage

```sh
./envcheck.py
./envcheck.py --json
```

Each finding has a check name, a status (`ok`, `warn`, `error`) and a message.
The human format prints one line per finding plus a summary; JSON adds a
`summary` object with counts. Warnings are real problems but usually not fatal;
errors mean a core variable is unset or points at nothing.

## Exit codes

| code | meaning |
|------|---------|
| 0 | no warnings or errors |
| 1 | at least one warning or error was found |
| 2 | invalid arguments |

## Test

`./envcheck.py --self-test` audits one fully valid synthetic environment and one
broken one, asserting that duplicate/missing/relative PATH entries, a missing
HOME, unset LANG and TERM=dumb are all reported with the right severity. The
temporary directory is removed afterwards.
