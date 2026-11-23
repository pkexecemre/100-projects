# ascii-table

Read CSV or JSON rows and print them as an aligned ASCII table. Cells longer
than `--max-width` are truncated with `...`, and all borders line up even when
input is ragged.

## Usage

```sh
python3 ascii_table.py people.csv
python3 ascii_table.py data.json
python3 ascii_table.py --format json --max-width 20 data.txt
cat people.csv | python3 ascii_table.py --no-header
python3 ascii_table.py data.csv --delimiter tab
```

CSV uses the first row as the header unless `--no-header` is given; for JSON
rows, `--no-header` likewise hides the key/first-row header. JSON may be
an array of objects (columns are the union of keys, in first-seen order), an
array of arrays (first row is the header), or a single object (rendered as one
row). Nested values are compacted to single-line JSON; newlines inside cells
become spaces. Format is auto-detected from the `.json` extension, otherwise
CSV; override with `--format csv|json`.

Example:

```
+------+-----+
| name | age |
+------+-----+
| Ada  | 36  |
| Bob  | 41  |
+------+-----+
```

Exit codes: `0` success, `2` for unreadable files, empty tables, malformed
CSV/JSON, or bad arguments.

## Test

```sh
python3 ascii_table.py --self-test
```

The self-test checks alignment, headers, truncation, CSV parsing with and
without headers, JSON object/list input, and nested value rendering.
