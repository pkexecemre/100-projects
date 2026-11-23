#!/usr/bin/env python3
"""Render CSV or JSON rows as an aligned ASCII table with cell truncation."""

import argparse
import csv
import io
import json
import sys


def cell_text(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"))
    return str(value)


def truncate(text, max_width):
    text = " ".join(cell_text(text).split())
    if len(text) <= max_width:
        return text
    if max_width <= 3:
        return text[:max_width]
    return text[:max_width - 3] + "..."


def render(header, rows, max_width=40):
    """Return table lines. header may be None; rows are lists of cells."""
    rows = [[cell_text(cell) for cell in row] for row in rows]
    header = [cell_text(cell) for cell in header] if header is not None else None
    columns = max([len(header or [])] + [len(row) for row in rows] + [0])
    if columns == 0:
        raise ValueError("no columns to render")
    if header is not None:
        header = header + [""] * (columns - len(header))
    fixed_rows = [row + [""] * (columns - len(row)) for row in rows]
    header = [truncate(cell, max_width) for cell in header] if header else None
    fixed_rows = [[truncate(cell, max_width) for cell in row]
                  for row in fixed_rows]

    widths = [0] * columns
    if header:
        widths = [len(cell) for cell in header]
    for row in fixed_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    border = "+" + "+".join("-" * (width + 2) for width in widths) + "+"

    def line(cells):
        return "| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells)) + " |"

    out = [border]
    if header:
        out.extend([line(header), border])
    out.extend(line(row) for row in fixed_rows)
    if not header or fixed_rows:
        out.append(border)
    return "\n".join(out)


def parse_csv(text, delimiter, no_header):
    rows = [row for row in csv.reader(io.StringIO(text), delimiter=delimiter)
            if any(cell.strip() for cell in row)]
    if not rows:
        raise ValueError("no CSV rows found")
    if no_header:
        return None, rows
    return rows[0], rows[1:]


def parse_json(text, no_header):
    data = json.loads(text)
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or not data:
        raise ValueError("JSON must be a non-empty array of objects or arrays")
    if all(isinstance(row, dict) for row in data):
        header = []
        for row in data:
            for key in row:
                if key not in header:
                    header.append(key)
        rows = [[row.get(key, "") for key in header] for row in data]
        return (None, rows) if no_header else (header, rows)
    if all(isinstance(row, list) for row in data):
        if no_header:
            return None, data
        return data[0], data[1:]
    raise ValueError("JSON must be a non-empty array of objects or arrays")


def self_test():
    header = ["name", "age", "city"]
    rows = [["Ada", "36", "London"], ["Bob", "41", "Paris"]]
    table = render(header, rows, max_width=20)
    lines = table.splitlines()
    assert lines[0] == "+------+-----+--------+"
    assert len({len(line) for line in lines}) == 1
    assert lines[1] == "| name | age | city   |"
    assert "| Bob  | 41  | Paris  |" in lines
    assert "| Ada  | 36  | London |" in lines

    long = render(["id", "note"], [["1", "x" * 100]], max_width=12)
    assert "xxxxxxxxx..." in long
    assert all(len(line) == len(long.splitlines()[0]) for line in long.splitlines())

    parsed_header, parsed_rows = parse_csv("a,b\n1,2\n3,4\n", ",", False)
    assert parsed_header == ["a", "b"] and parsed_rows == [["1", "2"], ["3", "4"]]
    no_header, all_rows = parse_csv("1,2\n3,4\n", ",", True)
    assert no_header is None and len(all_rows) == 2

    json_header, json_rows = parse_json('[{"a": 1}, {"a": 2, "b": true}]', False)
    assert json_header == ["a", "b"]
    assert json_rows == [[1, ""], [2, True]]
    assert "b" in render(json_header, json_rows)
    assert "true" in render(json_header, json_rows)
    no_json_header, _ = parse_json('[{"a": 1}]', True)
    assert no_json_header is None

    list_header, list_rows = parse_json('[[1, "x"], [2, "y"]]', False)
    assert list_header == [1, "x"] and list_rows == [[2, "y"]]
    assert "+---+" in render(None, [["a"]])
    header_only = render(["h"], [], max_width=20)
    assert header_only.splitlines() == ["+---+", "| h |", "+---+"]
    print("self-test: 15 checks passed")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Print CSV or JSON rows as an aligned ASCII table.")
    parser.add_argument("file", nargs="?", default="-",
                        help="input file, or - for stdin (default)")
    parser.add_argument("--format", choices=["auto", "csv", "json"], default="auto",
                        help="input format (default auto by extension)")
    parser.add_argument("--no-header", action="store_true",
                        help="treat every row as data")
    parser.add_argument("--delimiter", default=",",
                        help="CSV delimiter, or 'tab' (default ',')")
    parser.add_argument("--max-width", type=int, default=40, metavar="N",
                        help="maximum cell width before truncation (default 40)")
    parser.add_argument("--self-test", action="store_true",
                        help="run offline checks and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        self_test()
        return 0
    if args.max_width < 4:
        parser.error("--max-width must be at least 4")
    if args.delimiter == "tab":
        args.delimiter = "\t"
    if len(args.delimiter) != 1:
        parser.error("--delimiter must be one character or 'tab'")

    fmt = args.format
    if fmt == "auto":
        lowered = args.file.lower()
        fmt = "json" if lowered.endswith(".json") else "csv"

    try:
        if args.file == "-":
            text = sys.stdin.read()
        else:
            with open(args.file, encoding="utf-8-sig") as handle:
                text = handle.read()
        if fmt == "json":
            header, rows = parse_json(text, args.no_header)
        else:
            header, rows = parse_csv(text, args.delimiter, args.no_header)
        print(render(header, rows, args.max_width))
    except (OSError, UnicodeDecodeError, ValueError, csv.Error,
            json.JSONDecodeError) as exc:
        print("ascii-table: error: %s" % exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
