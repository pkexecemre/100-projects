#!/usr/bin/env python3
"""CSV expense log with monthly summaries and category totals."""

import argparse
import csv
import io
import os
import sys
import tempfile
from datetime import date, datetime

DEFAULT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.csv")
FIELDS = ["date", "amount", "category", "note"]


def load(path):
    rows = []
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames != FIELDS:
                raise ValueError(f"expected header {','.join(FIELDS)}")
            for line, raw in enumerate(reader, 2):
                try:
                    day = datetime.strptime(raw["date"], "%Y-%m-%d").date()
                    amount = round(float(raw["amount"]), 2)
                except (TypeError, ValueError):
                    print(f"warning: skipping malformed row {line}", file=sys.stderr)
                    continue
                if amount <= 0:
                    print(f"warning: skipping non-positive amount on row {line}", file=sys.stderr)
                    continue
                rows.append({
                    "date": day,
                    "amount": amount,
                    "category": (raw["category"] or "uncategorized").strip(),
                    "note": (raw["note"] or "").strip(),
                })
    except FileNotFoundError:
        return []
    except OSError as exc:
        sys.exit(f"error: cannot read {path}: {exc}")
    except ValueError as exc:
        sys.exit(f"error: cannot parse {path}: {exc}")
    return rows


def save(path, rows):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for row in sorted(rows, key=lambda item: item["date"]):
            writer.writerow({
                "date": row["date"].isoformat(),
                "amount": f"{row['amount']:.2f}",
                "category": row["category"],
                "note": row["note"],
            })
    os.replace(tmp, path)


def add_expense(rows, amount, category, note="", when=None):
    amount = round(float(amount), 2)
    if amount <= 0:
        raise ValueError("amount must be greater than zero")
    category = category.strip()
    if not category:
        raise ValueError("category must not be empty")
    row = {
        "date": when or date.today(),
        "amount": amount,
        "category": category,
        "note": note.strip(),
    }
    rows.append(row)
    return row


def summarize(rows, month):
    selected = [row for row in rows if row["date"].strftime("%Y-%m") == month]
    total = sum(row["amount"] for row in selected)
    categories = {}
    for row in selected:
        categories[row["category"]] = categories.get(row["category"], 0.0) + row["amount"]
    return selected, total, categories


def show_summary(rows, month, out=sys.stdout):
    selected, total, categories = summarize(rows, month)
    if not selected:
        out.write(f"no expenses for {month}\n")
        return
    out.write(f"Expenses for {month}\n")
    out.write(f"  entries: {len(selected)}\n")
    out.write(f"  total:   {total:.2f}\n")
    out.write("  by category:\n")
    for category, amount in sorted(categories.items(), key=lambda item: (-item[1], item[0])):
        share = 100 * amount / total if total else 0
        out.write(f"    {category:<20} {amount:>10.2f}  {share:5.1f}%\n")


def show_list(rows, month=None, out=sys.stdout):
    selected = [row for row in rows if month is None or row["date"].strftime("%Y-%m") == month]
    selected.sort(key=lambda row: row["date"])
    if not selected:
        out.write("no expenses recorded\n")
        return
    for row in selected:
        note = f"  # {row['note']}" if row["note"] else ""
        out.write(f"{row['date'].isoformat()}  {row['category']:<16} {row['amount']:>9.2f}{note}\n")


def date_type(value):
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError("date must be YYYY-MM-DD")
    if parsed.isoformat() != value:
        raise argparse.ArgumentTypeError("date must be YYYY-MM-DD")
    return parsed


def month_type(value):
    if len(value) != 7:
        raise argparse.ArgumentTypeError("month must be YYYY-MM")
    try:
        datetime.strptime(value + "-01", "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError("month must be YYYY-MM")
    return value


def amount_type(value):
    try:
        amount = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("amount must be a number")
    if amount <= 0:
        raise argparse.ArgumentTypeError("amount must be greater than zero")
    return round(amount, 2)


def self_test():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "expenses.csv")
        rows = load(path)
        add_expense(rows, 12.5, "food", "lunch", date(2026, 11, 2))
        add_expense(rows, 7.25, "food", when=date(2026, 11, 3))
        add_expense(rows, 30, "transport", when=date(2026, 10, 30))
        save(path, rows)
        loaded = load(path)
        assert len(loaded) == 3
        selected, total, categories = summarize(loaded, "2026-11")
        assert len(selected) == 2
        assert abs(total - 19.75) < 0.001
        assert abs(categories["food"] - 19.75) < 0.001
        buffer = io.StringIO()
        show_summary(loaded, "2026-11", buffer)
        assert "19.75" in buffer.getvalue() and "food" in buffer.getvalue()
        buffer = io.StringIO()
        show_list(loaded, "2026-11", buffer)
        assert "transport" not in buffer.getvalue()
        assert "lunch" in buffer.getvalue()
        empty = io.StringIO()
        show_summary(loaded, "2025-01", empty)
        assert "no expenses" in empty.getvalue()
        try:
            add_expense(loaded, 0, "food")
        except ValueError:
            pass
        else:
            raise AssertionError("zero amount accepted")
        try:
            add_expense(loaded, 1, "  ")
        except ValueError:
            pass
        else:
            raise AssertionError("empty category accepted")
        assert date_type("2026-11-23") == date(2026, 11, 23)
        assert month_type("2026-11") == "2026-11"
    print("self-test OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Log expenses to CSV and summarize them by month and category.",
        epilog="Exit codes: 0 success, 1 storage or input error, 2 usage error.",
    )
    ap.add_argument("--file", default=DEFAULT_FILE, help="expense CSV file")
    ap.add_argument("--self-test", action="store_true", help="run built-in checks")
    sub = ap.add_subparsers(dest="command", metavar="command")

    add_parser = sub.add_parser("add", help="record an expense")
    add_parser.add_argument("amount", type=amount_type)
    add_parser.add_argument("category")
    add_parser.add_argument("-n", "--note", default="")
    add_parser.add_argument("--date", type=date_type, default=None, metavar="YYYY-MM-DD")

    list_parser = sub.add_parser("list", help="list expenses")
    list_parser.add_argument("--month", type=month_type, default=None, metavar="YYYY-MM")

    summary_parser = sub.add_parser("summary", help="monthly totals by category")
    summary_parser.add_argument("--month", type=month_type, default=None, metavar="YYYY-MM")

    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.command:
        ap.print_help()
        return 2

    rows = load(args.file)
    if args.command == "add":
        try:
            row = add_expense(rows, args.amount, args.category, args.note, args.date)
            save(args.file, rows)
        except (OSError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"added: {row['amount']:.2f} {row['category']} on {row['date'].isoformat()}")
    elif args.command == "list":
        show_list(rows, args.month)
    elif args.command == "summary":
        month = args.month or date.today().strftime("%Y-%m")
        show_summary(rows, month)
    return 0


if __name__ == "__main__":
    sys.exit(main())
