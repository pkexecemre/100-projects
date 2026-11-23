#!/usr/bin/env python3
"""Track books and reading status in a JSON file."""

import argparse
import io
import json
import os
import sys
import tempfile
from datetime import date

DEFAULT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reading-list.json")
STATUSES = ["want", "reading", "read"]
ALIASES = {
    "want": "want",
    "to-read": "want",
    "todo": "want",
    "reading": "reading",
    "current": "reading",
    "read": "read",
    "done": "read",
    "finished": "read",
}


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return {"books": []}
    except (OSError, ValueError) as exc:
        sys.exit(f"error: cannot read {path}: {exc}")
    raw_books = data.get("books") if isinstance(data, dict) else None
    if not isinstance(raw_books, list):
        sys.exit(f"error: {path} must contain an object with a 'books' list")
    books = []
    for item in raw_books:
        if not isinstance(item, dict) or not isinstance(item.get("id"), int):
            continue
        title = str(item.get("title", "")).strip()
        if not title:
            continue
        try:
            rating = max(0, min(5, int(item.get("rating", 0))))
        except (TypeError, ValueError):
            rating = 0
        status = str(item.get("status", "want"))
        books.append({
            "id": item["id"],
            "title": title,
            "author": str(item.get("author", "")).strip(),
            "status": status if status in STATUSES else "want",
            "rating": rating,
            "added": str(item.get("added", "")),
        })
    return {"books": books}


def save(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def add_book(data, title, author="", status="want", rating=0):
    title = title.strip()
    if not title:
        raise ValueError("title must not be empty")
    if status not in STATUSES:
        raise ValueError(f"status must be one of: {', '.join(STATUSES)}")
    if not 0 <= rating <= 5:
        raise ValueError("rating must be between 0 and 5")
    next_id = max((book["id"] for book in data["books"]), default=0) + 1
    book = {
        "id": next_id,
        "title": title,
        "author": author.strip(),
        "status": status,
        "rating": int(rating),
        "added": date.today().isoformat(),
    }
    data["books"].append(book)
    return book


def get_book(data, book_id):
    for book in data["books"]:
        if book["id"] == book_id:
            return book
    return None


def update_book(data, book_id, status=None, rating=None):
    book = get_book(data, book_id)
    if book is None:
        raise KeyError(f"no book with ID {book_id}")
    if status is not None:
        book["status"] = status
    if rating is not None:
        book["rating"] = int(rating)
    return book


def remove_book(data, book_id):
    book = get_book(data, book_id)
    if book is None:
        return False
    data["books"].remove(book)
    return True


def show_books(books, out=sys.stdout):
    if not books:
        out.write("no books\n")
        return
    order = {status: index for index, status in enumerate(STATUSES)}
    books = sorted(books, key=lambda book: (order[book["status"]], book["id"]))
    out.write(f"{'ID':>3}  {'STATUS':<7} {'RATING':<6}  TITLE\n")
    for book in books:
        rating = f"{book['rating']}/5" if book["rating"] else "-"
        author = f" ({book['author']})" if book["author"] else ""
        out.write(f"{book['id']:>3}  {book['status']:<7} {rating:<6}  {book['title']}{author}\n")


def status_type(value):
    status = ALIASES.get(value.strip().lower())
    if status is None:
        raise argparse.ArgumentTypeError(
            f"status must be one of: {', '.join(STATUSES)}"
        )
    return status


def rating_type(value):
    try:
        rating = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("rating must be an integer from 0 to 5")
    if not 0 <= rating <= 5:
        raise argparse.ArgumentTypeError("rating must be between 0 and 5")
    return rating


def self_test():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "reading-list.json")
        data = load(path)
        first = add_book(data, "Dune", "Frank Herbert", "reading", 5)
        second = add_book(data, "Neuromancer", "William Gibson")
        assert first["id"] == 1 and second["id"] == 2
        assert second["status"] == "want" and second["rating"] == 0

        update_book(data, 2, status="read", rating=4)
        assert get_book(data, 2)["rating"] == 4
        try:
            update_book(data, 99, status="read")
        except KeyError:
            pass
        else:
            raise AssertionError("missing book was updated")

        save(path, data)
        loaded = load(path)
        assert len(loaded["books"]) == 2
        buffer = io.StringIO()
        show_books(loaded["books"], buffer)
        report = buffer.getvalue()
        assert "Dune" in report and "4/5" in report

        filtered = [book for book in loaded["books"] if book["status"] == "read"]
        assert len(filtered) == 1 and filtered[0]["title"] == "Neuromancer"
        assert remove_book(loaded, 1)
        assert not remove_book(loaded, 1)
        save(path, loaded)
        assert len(load(path)["books"]) == 1
        assert status_type("finished") == "read"
        assert rating_type("3") == 3
    print("self-test OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Keep a reading list with status and star ratings.",
        epilog="Statuses: want, reading, read. Exit codes: 0 success, "
        "1 missing book or storage error, 2 usage error.",
    )
    ap.add_argument("--file", default=DEFAULT_FILE, help="reading list JSON file")
    ap.add_argument("--self-test", action="store_true", help="run built-in checks")
    sub = ap.add_subparsers(dest="command", metavar="command")

    add_parser = sub.add_parser("add", help="add a book")
    add_parser.add_argument("title")
    add_parser.add_argument("-a", "--author", default="")
    add_parser.add_argument("--status", type=status_type, default="want")
    add_parser.add_argument("--rating", type=rating_type, default=0)

    list_parser = sub.add_parser("list", help="list books")
    list_parser.add_argument("--status", type=status_type, default=None)

    update_parser = sub.add_parser("update", help="change status or rating")
    update_parser.add_argument("id", type=int)
    update_parser.add_argument("--status", type=status_type, default=None)
    update_parser.add_argument("--rating", type=rating_type, default=None)

    remove_parser = sub.add_parser("remove", help="delete a book")
    remove_parser.add_argument("id", type=int)

    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.command:
        ap.print_help()
        return 2

    data = load(args.file)
    try:
        if args.command == "add":
            book = add_book(data, args.title, args.author, args.status, args.rating)
            save(args.file, data)
            print(f"added #{book['id']}: {book['title']} [{book['status']}]")
        elif args.command == "list":
            books = [book for book in data["books"]
                     if args.status is None or book["status"] == args.status]
            show_books(books)
        elif args.command == "update":
            if args.status is None and args.rating is None:
                print("error: give --status and/or --rating", file=sys.stderr)
                return 1
            book = update_book(data, args.id, args.status, args.rating)
            save(args.file, data)
            print(f"updated #{book['id']}: {book['title']} [{book['status']}]")
        elif args.command == "remove":
            if not remove_book(data, args.id):
                print(f"error: no book with ID {args.id}", file=sys.stderr)
                return 1
            save(args.file, data)
            print(f"removed #{args.id}")
    except KeyError as exc:
        print(f"error: {exc.args[0]}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
