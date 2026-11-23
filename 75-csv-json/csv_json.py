#!/usr/bin/env python3
"""Convert CSV to JSON with header handling and optional type inference."""

import argparse
import csv
import io
import json
import re
import sys

INT_RE = re.compile(r"^[+-]?(?:0|[1-9]\d*)$")
FLOAT_RE = re.compile(r"^[+-]?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?$")


def infer_value(cell, infer, empty_null):
    if cell == "" and empty_null:
        return None
    if not infer:
        return cell
    lowered = cell.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    if INT_RE.fullmatch(cell):
        return int(cell)
    if FLOAT_RE.fullmatch(cell) and ("." in cell or "e" in lowered):
        return float(cell)
    return cell


def convert(rows, has_header=True, infer=False, empty_null=False):
    if not rows:
        return []
    width = max(len(row) for row in rows)
    if has_header:
        header, data = rows[0], rows[1:]
    else:
        header, data = [], rows

    names = []
    for index in range(width):
        candidate = header[index].strip() if index < len(header) else ""
        if not candidate:
            candidate = f"column_{index + 1}"
        name, suffix = candidate, 2
        while name in names:
            name = f"{candidate}_{suffix}"
            suffix += 1
        names.append(name)

    records = []
    for row in data:
        record = {}
        for index, name in enumerate(names):
            cell = row[index] if index < len(row) else ""
            record[name] = infer_value(cell, infer, empty_null)
        records.append(record)
    return records


def read_input(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return handle.read()


def self_test():
    rows = list(csv.reader(io.StringIO(
        "name,age,active,score\nAda,36,true,9.5\nBob,,FALSE,\n")))
    records = convert(rows, infer=True)
    assert records[0] == {"name": "Ada", "age": 36, "active": True, "score": 9.5}
    assert records[1] == {"name": "Bob", "age": "", "active": False, "score": ""}
    strict = convert(rows)
    assert strict[0]["age"] == "36" and strict[0]["active"] == "true"
    nulls = convert(rows, empty_null=True, infer=True)
    assert nulls[1]["age"] is None and nulls[1]["score"] is None

    ragged = list(csv.reader(io.StringIO("a,a,\nx,1,extra,overflow\n")))
    deduped = convert(ragged)
    assert list(deduped[0]) == ["a", "a_2", "column_3", "column_4"]
    assert deduped[0]["column_4"] == "overflow"

    no_header = convert(list(csv.reader(io.StringIO("1,2\n3,4\n"))), has_header=False,
                        infer=True)
    assert no_header == [{"column_1": 1, "column_2": 2},
                         {"column_1": 3, "column_2": 4}]

    leading = convert(list(csv.reader(io.StringIO("zip\n007\n"))), infer=True)
    assert leading[0]["zip"] == "007"
    assert convert([]) == []
    print("self-test: all checks passed")


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--self-test" in argv:
        self_test()
        return 0

    ap = argparse.ArgumentParser(
        description="Convert CSV (file or stdin) to a JSON array of objects.",
        epilog="Examples: csv_json.py data.csv --infer | cat data.csv | csv_json.py",
    )
    ap.add_argument("file", nargs="?", default="-", help="CSV file, or - for stdin")
    ap.add_argument("-d", "--delimiter", default=",", help="field delimiter (default ,)")
    ap.add_argument("--no-header", action="store_true",
                    help="first row is data; columns become column_1..N")
    ap.add_argument("--infer", action="store_true",
                    help="convert ints, floats, true/false, null (leading zeros stay strings)")
    ap.add_argument("--empty-null", action="store_true", help="treat empty cells as null")
    ap.add_argument("--indent", type=int, default=2, help="JSON indent, 0 for compact")
    ap.add_argument("-o", "--output", help="write JSON to a file instead of stdout")
    args = ap.parse_args(argv)

    if len(args.delimiter) != 1 or args.delimiter in "\r\n\"":
        print("error: --delimiter must be one character other than CR, LF or double quote",
              file=sys.stderr)
        return 2
    if args.indent < 0:
        print("error: --indent must be >= 0", file=sys.stderr)
        return 2
    try:
        text = read_input(args.file)
    except OSError as exc:
        print(f"error: cannot read {args.file}: {exc}", file=sys.stderr)
        return 1
    except UnicodeError as exc:
        print(f"error: {args.file} is not valid UTF-8: {exc}", file=sys.stderr)
        return 1
    if text.startswith("\ufeff"):
        text = text[1:]
    try:
        rows = [row for row in csv.reader(io.StringIO(text), delimiter=args.delimiter) if row]
    except csv.Error as exc:
        print(f"error: malformed CSV: {exc}", file=sys.stderr)
        return 1

    records = convert(rows, has_header=not args.no_header,
                      infer=args.infer, empty_null=args.empty_null)
    rendered = json.dumps(records, indent=args.indent if args.indent else None,
                          ensure_ascii=True)
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(rendered + "\n")
        except OSError as exc:
            print(f"error: cannot write {args.output}: {exc}", file=sys.stderr)
            return 1
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
