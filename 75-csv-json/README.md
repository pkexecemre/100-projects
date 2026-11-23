# 75 - csv-json

Read CSV from a file or stdin and emit a JSON array of objects. Handles
duplicate/blank headers, ragged rows, and optional type inference.

## Usage

```console
$ printf 'name,age,active\nAda,36,true\nBob,,false\n' | ./csv_json.py --infer
[
  {
    "name": "Ada",
    "age": 36,
    "active": true
  },
  {
    "name": "Bob",
    "age": "",
    "active": false
  }
]
$ ./csv_json.py data.csv --delimiter ';' --indent 0 -o data.json
```

Behavior:

- the first row is the header unless `--no-header` is given
- empty or duplicate header names become `column_N` / `name_2`, `name_3`
- short rows are padded with `""`; extra fields get generated `column_N` names
  (the header is extended to the widest row)
- UTF-8 input with a BOM is accepted; quoted CSV fields are handled by `csv`

Type inference (`--infer`) converts:

- integers without leading zeros (`007` stays a string)
- floats and scientific notation (`9.5`, `1e3`)
- `true` / `false` (any case) and `null`
- empty cells to `null` only with `--empty-null`

## Options

- `-d, --delimiter CHAR` - field delimiter (default `,`)
- `--no-header` - treat every row as data
- `--infer` - enable type inference
- `--empty-null` - empty cell becomes JSON `null`
- `--indent N` - JSON indentation, `0` for compact (default 2)
- `-o, --output FILE` - write to a file
- `--self-test` - run built-in conversion checks

## Exit codes

- `0` success
- `1` unreadable input file, malformed CSV, unwritable output
- `2` invalid delimiter or negative indent

## Self-test

```console
$ ./csv_json.py --self-test
self-test: all checks passed
```
