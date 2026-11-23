#!/usr/bin/env python3
"""Summarize CSV columns: numeric ranges and categorical top values."""

import argparse
import csv
import json
import sys
from collections import Counter


def analyze(rows, has_header=True, top=5):
    """Return stats for each column of a list of raw string rows."""
    if not rows:
        raise ValueError("no data found")

    if has_header:
        header = [cell.strip() or "column_%d" % (i + 1) for i, cell in enumerate(rows[0])]
        data = rows[1:]
    else:
        header = []
        data = rows

    width = max([len(header)] + [len(row) for row in data])
    if width == 0:
        raise ValueError("no columns found")
    while len(header) < width:
        header.append("column_%d" % (len(header) + 1))

    if has_header and len(data) == 0:
        raise ValueError("header found but no data rows")

    stats = []
    for index, name in enumerate(header):
        values = [row[index].strip() for row in data
                  if index < len(row) and row[index].strip() != ""]
        missing = len(data) - len(values)
        numbers = []
        numeric = bool(values)
        for value in values:
            try:
                numbers.append(float(value))
            except ValueError:
                numeric = False
                break

        if numeric:
            total = sum(numbers)
            mean = total / len(numbers)
            stats.append({
                "name": name,
                "type": "numeric",
                "count": len(numbers),
                "missing": missing,
                "unique": len(set(numbers)),
                "min": numbers[0] if len(numbers) == 1 else min(numbers),
                "max": numbers[0] if len(numbers) == 1 else max(numbers),
                "mean": mean,
            })
        else:
            counts = Counter(values)
            stats.append({
                "name": name,
                "type": "categorical",
                "count": len(values),
                "missing": missing,
                "unique": len(counts),
                "top": [{"value": value, "count": count}
                        for value, count in counts.most_common(top)],
            })
    return {"rows": len(data), "columns": stats}


def fmt(value):
    """Compact numeric formatting that keeps integers integral."""
    if value == int(value) and abs(value) < 1e15:
        return str(int(value))
    return ("%.6g" % value)


def render(result):
    """Render a fixed-width ASCII summary table."""
    headers = ["name", "type", "count", "missing", "summary"]
    body = []
    for col in result["columns"]:
        if col["type"] == "numeric":
            summary = "min=%s max=%s mean=%s" % (
                fmt(col["min"]), fmt(col["max"]), fmt(col["mean"]))
        else:
            top = ", ".join("%s(%d)" % (item["value"], item["count"])
                            for item in col["top"]) or "-"
            summary = "top=" + top
        body.append([col["name"], col["type"], str(col["count"]),
                     str(col["missing"]), summary])

    widths = [len(h) for h in headers]
    for row in body:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    lines = ["  ".join(headers[i].ljust(widths[i]) for i in range(len(headers))),
             "  ".join("-" * widths[i] for i in range(len(headers)))]
    for row in body:
        lines.append("  ".join(row[i].ljust(widths[i]) for i in range(len(row))).rstrip())
    return "\n".join(lines)


def load(path, delimiter):
    if path == "-":
        stream = sys.stdin
        close = False
    else:
        stream = open(path, newline="", encoding="utf-8-sig")
        close = True
    try:
        reader = csv.reader(stream, delimiter=delimiter)
        return [row for row in reader if any(cell.strip() for cell in row)]
    finally:
        if close:
            stream.close()


def self_test():
    sample = (
        "name,age,city\n"
        "Ada,36,London\n"
        "Bob,41,Paris\n"
        "Cy,,Paris\n"
        "Dee,29,Berlin\n"
    )
    rows = list(csv.reader(sample.splitlines()))
    result = analyze(rows, top=2)
    assert result["rows"] == 4
    age, city = result["columns"][1], result["columns"][2]
    assert age["type"] == "numeric" and age["count"] == 3 and age["missing"] == 1
    assert age["min"] == 29 and age["max"] == 41
    assert abs(age["mean"] - (36 + 41 + 29) / 3) < 1e-9
    assert city["type"] == "categorical" and city["unique"] == 3
    assert city["top"][0] == {"value": "Paris", "count": 2}
    assert len(city["top"]) == 2

    no_header = analyze([["1", "x"], ["2", "y"]], has_header=False)
    assert no_header["columns"][0]["type"] == "numeric"
    assert no_header["columns"][0]["name"] == "column_1"

    rendered = render(result)
    assert rendered.splitlines()[0].startswith("name")
    assert "min=29" in rendered and "Paris(2)" in rendered
    try:
        analyze([])
    except ValueError:
        pass
    else:
        raise AssertionError("empty input should fail")
    print("self-test: 12 checks passed")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Column statistics for CSV data (numeric ranges and top values).")
    parser.add_argument("file", nargs="?", default="-",
                        help="CSV file, or - for stdin (default)")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--no-header", action="store_true",
                        help="treat the first row as data")
    parser.add_argument("--top", type=int, default=5, metavar="N",
                        help="number of top categorical values (default 5)")
    parser.add_argument("--delimiter", default=",",
                        help="field delimiter, or 'tab' (default ',')")
    parser.add_argument("--self-test", action="store_true",
                        help="run offline checks and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        self_test()
        return 0
    if args.top < 1:
        parser.error("--top must be at least 1")
    if args.delimiter == "tab":
        args.delimiter = "\t"
    if len(args.delimiter) != 1:
        parser.error("--delimiter must be one character or 'tab'")

    try:
        rows = load(args.file, args.delimiter)
        result = analyze(rows, has_header=not args.no_header, top=args.top)
    except (OSError, ValueError, csv.Error) as exc:
        print("csv-stats: error: %s" % exc, file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=False))
    else:
        print(render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
