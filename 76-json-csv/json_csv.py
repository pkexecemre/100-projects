#!/usr/bin/env python3
"""Convert JSON records to CSV with flattened columns and stable ordering."""

import argparse
import csv
import io
import json
import sys


def leaf(value):
    """Render a non-record value the way it should appear in a CSV cell."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    return value


def flatten(record, prefix="", out=None):
    """Flatten nested objects into dot-separated keys; lists become JSON text."""
    if out is None:
        out = {}
    for key, value in record.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            if value:
                flatten(value, name, out)
            else:
                out[name] = "{}"
        else:
            out[name] = leaf(value)
    return out


def records_from(data):
    """Normalize supported JSON shapes into a list of flat dictionaries."""
    if isinstance(data, list):
        if not data:
            return []
        if all(isinstance(item, dict) for item in data):
            return [flatten(item) for item in data]
        return [{"value": leaf(item)} for item in data]
    if isinstance(data, dict):
        if data and all(isinstance(value, list) for value in data.values()):
            lengths = {len(value) for value in data.values()}
            if len(lengths) == 1:
                count = lengths.pop()
                return [flatten({key: value[i] for key, value in data.items()})
                        for i in range(count)]
        if not data:
            return [{"value": "{}"}]
        return [flatten(data)]
    return [{"value": leaf(data)}]


def columns_for(records, sort_columns=False):
    seen = []
    for record in records:
        for key in record:
            if key not in seen:
                seen.append(key)
    return sorted(seen) if sort_columns else seen


def cell_text(value, null_text):
    if value is None:
        return null_text
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def render(records, delimiter=",", include_header=True, null_text="", sort_columns=False):
    columns = columns_for(records, sort_columns)
    if not columns:
        return ""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\n")
    if include_header and columns:
        writer.writerow(columns)
    for record in records:
        writer.writerow([cell_text(record.get(column), null_text) for column in columns])
    return buffer.getvalue()


def read_json(path):
    if path == "-":
        text = sys.stdin.read()
        if text.startswith("\ufeff"):
            text = text[1:]
        return json.loads(text)
    with open(path, encoding="utf-8-sig") as handle:
        return json.load(handle)


def self_test():
    data = [
        {"id": 1, "meta": {"a": 1, "b": None}, "tags": ["x", "y"], "ok": True},
        {"id": 2, "extra": "v", "meta": {"a": 2}},
    ]
    records = records_from(data)
    assert records[0]["meta.a"] == 1 and records[0]["meta.b"] is None
    assert records[0]["tags"] == '["x","y"]'
    assert records[0]["ok"] == "true"
    assert columns_for(records) == ["id", "meta.a", "meta.b", "tags", "ok", "extra"]
    text = render(records)
    assert text.splitlines()[0] == "id,meta.a,meta.b,tags,ok,extra"
    assert text.splitlines()[1] == '1,1,,"[""x"",""y""]",true,'
    assert render([{"b": 1, "a": 2}], sort_columns=True).splitlines()[0] == "a,b"

    assert records_from([1, 2]) == [{"value": 1}, {"value": 2}]
    assert records_from({"a": "b"}) == [{"a": "b"}]
    columnar = records_from({"x": [1, 2], "y": [3, 4]})
    assert columnar == [{"x": 1, "y": 3}, {"x": 2, "y": 4}]
    assert records_from({"deep": {"deeper": {"v": False}}}) == [{"deep.deeper.v": "false"}]
    assert records_from({}) == [{"value": "{}"}]
    assert render([], include_header=True) == ""
    assert render([{"a": None}], null_text="NULL").strip() == "a\nNULL"
    print("self-test: all checks passed")


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--self-test" in argv:
        self_test()
        return 0

    ap = argparse.ArgumentParser(
        description="Convert JSON records to CSV with flattened columns.",
        epilog="Examples: json_csv.py data.json | cat data.json | json_csv.py -",
    )
    ap.add_argument("file", nargs="?", default="-", help="JSON file, or - for stdin")
    ap.add_argument("-d", "--delimiter", default=",", help="CSV delimiter (default ,)")
    ap.add_argument("--no-header", action="store_true", help="omit the header row")
    ap.add_argument("--sort-columns", action="store_true",
                    help="alphabetical columns instead of first-appearance order")
    ap.add_argument("--null", dest="null_text", default="",
                    help="text used for JSON null (default empty)")
    ap.add_argument("-o", "--output", help="write CSV to a file instead of stdout")
    args = ap.parse_args(argv)

    if len(args.delimiter) != 1 or args.delimiter in "\r\n\"":
        print("error: --delimiter must be one character other than CR, LF or double quote",
              file=sys.stderr)
        return 2
    try:
        data = read_json(args.file)
    except OSError as exc:
        print(f"error: cannot read {args.file}: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON: {exc}", file=sys.stderr)
        return 1
    except UnicodeError as exc:
        print(f"error: {args.file} is not valid UTF-8: {exc}", file=sys.stderr)
        return 1

    try:
        records = records_from(data)
    except (TypeError, ValueError) as exc:
        print(f"error: unsupported JSON structure: {exc}", file=sys.stderr)
        return 1
    text = render(records, args.delimiter, not args.no_header,
                  args.null_text, args.sort_columns)
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8", newline="") as handle:
                handle.write(text)
        except OSError as exc:
            print(f"error: cannot write {args.output}: {exc}", file=sys.stderr)
            return 1
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
