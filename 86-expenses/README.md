# 86 - expenses

A CSV expense log with a monthly summary and category breakdown. The file has a
fixed header (`date,amount,category,note`) and is sorted by date on every save,
so it stays readable in a spreadsheet.

## Usage

```sh
python3 expenses.py add 12.50 food -n "lunch"
python3 expenses.py add 30 transport --date 2026-11-01
python3 expenses.py list
python3 expenses.py list --month 2026-11
python3 expenses.py summary
python3 expenses.py summary --month 2026-10
python3 expenses.py --self-test
```

`summary` defaults to the current month and prints entry count, total, and
per-category totals with percentage shares. `add` rejects non-positive amounts
and empty categories; dates use `YYYY-MM-DD`. Malformed or non-positive rows in
an existing CSV are skipped with a warning on stderr rather than aborting the
whole file.

The store defaults to `expenses.csv` next to the script. Use
`--file /path/to/file.csv` to keep finances elsewhere.

## Exit codes

- `0` success
- `1` storage failure or rejected input
- `2` usage error (bad amount, date, or month)

`--self-test` writes a temporary CSV, checks round-trip persistence, monthly
filtering, category totals, output formatting, and input validation.
