# 76 - json-csv

Turn JSON into CSV. Nested objects are flattened with dot-separated column
names, columns keep a stable first-appearance order, and lists are written as
compact JSON inside their cell.

## Usage

```console
$ printf '[{"id":1,"meta":{"a":1}},{"id":2,"extra":"v"}]' | ./json_csv.py
id,meta.a,extra
1,1,
2,,v
$ ./json_csv.py - --sort-columns --null NULL
$ ./json_csv.py data.json -o data.csv --delimiter ';' --no-header
```

Supported top-level shapes:

- **array of objects** - one CSV row per object, nested dicts flattened
  (`{"meta":{"a":1}}` -> `meta.a`)
- **array of scalars** - a single `value` column
- **single object** - one row (nested objects flattened)
- **column-oriented object** - when every value is a list of equal length,
  each index becomes a row
- **scalar** - a single `value` row

Column set is the ordered union across all records (first appearance), or
alphabetical with `--sort-columns`. Missing fields become empty (or `--null`
text). Booleans render as `true`/`false`, `null` is configurable, and lists are
JSON-encoded. Output uses `\n` line endings.

## Options

- `-d, --delimiter CHAR` - output delimiter (default `,`)
- `--no-header` - omit the header row
- `--sort-columns` - alphabetical column order
- `--null TEXT` - replacement for JSON null (default empty)
- `-o, --output FILE` - write CSV to a file
- `--self-test` - run built-in shape/flattening checks

## Exit codes

- `0` success
- `1` unreadable input, invalid JSON, or unsupported structure
- `2` invalid delimiter

## Self-test

```console
$ ./json_csv.py --self-test
self-test: all checks passed
```
