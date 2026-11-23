# csv-stats

Summarize every column in a CSV file. Numeric columns report count, missing
values, unique values, min, max, and mean; everything else is treated as
categorical and reports the most common values. Pure Python standard library.

## Usage

```sh
python3 csv_stats.py data.csv
python3 csv_stats.py data.csv --json
cat data.csv | python3 csv_stats.py --no-header --top 3
python3 csv_stats.py data.tsv --delimiter tab
```

Options: `--json`, `--no-header`, `--top N` (default 5), `--delimiter CHAR|tab`.
Input is a file path or `-` (default) for stdin. The first row is the header
unless `--no-header` is given; ragged rows and blank lines are tolerated.

Example output:

```
name  type         count  missing  summary
----  -----------  -----  -------  -------
age   numeric      3      1        min=29 max=41 mean=35.3333
city  categorical  4      0        top=Paris(2), London(1), Berlin(1)
```

## Exit codes

- `0` success
- `2` unreadable file, empty input, malformed CSV, or bad arguments

## Test

```sh
python3 csv_stats.py --self-test
```

Offline checks cover CSV parsing, numeric statistics, missing values,
categorical ranking, rendering, and empty-input rejection.
