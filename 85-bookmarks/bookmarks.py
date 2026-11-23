#!/usr/bin/env python3
"""JSON bookmark manager with tags, search, and browser opening."""

import argparse
import io
import json
import os
import sys
import tempfile
import webbrowser
from datetime import date

DEFAULT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bookmarks.json")


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return {"bookmarks": []}
    except (OSError, ValueError) as exc:
        sys.exit(f"error: cannot read {path}: {exc}")
    books = data.get("bookmarks") if isinstance(data, dict) else None
    if not isinstance(books, list):
        sys.exit(f"error: {path} must contain an object with a 'bookmarks' list")
    clean = []
    for item in books:
        if not isinstance(item, dict) or not isinstance(item.get("url"), str):
            continue
        if not isinstance(item.get("id"), int):
            continue
        clean.append({
            "id": item["id"],
            "url": item["url"],
            "title": str(item.get("title") or item["url"]),
            "tags": [str(tag) for tag in item.get("tags", []) if str(tag).strip()],
            "added": str(item.get("added", "")),
        })
    return {"bookmarks": clean}


def save(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def clean_tags(values):
    if isinstance(values, str):
        values = [values]
    tags = []
    for value in values:
        for tag in str(value).split(","):
            tag = tag.strip().lower()
            if tag and tag not in tags:
                tags.append(tag)
    return tags


def add_bookmark(data, url, title="", tags=()):
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")
    if any(book["url"] == url for book in data["bookmarks"]):
        raise ValueError("that URL is already bookmarked")
    next_id = max((book["id"] for book in data["bookmarks"]), default=0) + 1
    book = {
        "id": next_id,
        "url": url,
        "title": (title.strip() or url),
        "tags": clean_tags(tags),
        "added": date.today().isoformat(),
    }
    data["bookmarks"].append(book)
    return book


def get_bookmark(data, book_id):
    for book in data["bookmarks"]:
        if book["id"] == book_id:
            return book
    return None


def remove_bookmark(data, book_id):
    book = get_bookmark(data, book_id)
    if book is None:
        return False
    data["bookmarks"].remove(book)
    return True


def find(data, query="", tag=None):
    query = query.lower()
    tag = tag.lower() if tag else None
    results = []
    for book in data["bookmarks"]:
        if tag and tag not in book["tags"]:
            continue
        haystack = " ".join([book["title"], book["url"], " ".join(book["tags"])]).lower()
        if not query or query in haystack:
            results.append(book)
    return results


def show(books, out=sys.stdout):
    if not books:
        out.write("no bookmarks\n")
        return
    id_width = max(2, max(len(str(book["id"])) for book in books))
    title_width = min(40, max(len(book["title"]) for book in books))
    out.write(f"{'ID':>{id_width}}  {'TITLE':<{title_width}}  {'TAGS':<16}  URL\n")
    for book in books:
        title = book["title"]
        if len(title) > title_width:
            title = title[: title_width - 3] + "..."
        tags = ",".join(book["tags"])
        if len(tags) > 16:
            tags = tags[:13] + "..."
        out.write(f"{book['id']:>{id_width}}  {title:<{title_width}}  {tags:<16}  {book['url']}\n")


def self_test():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "bookmarks.json")
        data = load(path)
        first = add_bookmark(data, "https://docs.python.org", "Python docs", ["python", "docs"])
        second = add_bookmark(data, "https://example.com", "Example", "misc,python")
        assert first["id"] == 1 and second["id"] == 2
        assert second["tags"] == ["misc", "python"]
        assert len(find(data, "python")) == 2
        assert find(data, "", "docs")[0]["id"] == 1
        assert find(data, "example")[0]["id"] == 2
        for url, title in (("ftp://bad", "bad"), ("https://example.com", "dupe")):
            try:
                add_bookmark(data, url, title)
            except ValueError:
                pass
            else:
                raise AssertionError(f"invalid bookmark accepted: {url}")
        save(path, data)
        loaded = load(path)
        assert len(loaded["bookmarks"]) == 2
        assert loaded["bookmarks"][1]["title"] == "Example"
        buffer = io.StringIO()
        show(loaded["bookmarks"], buffer)
        report = buffer.getvalue()
        assert "Python docs" in report and "https://example.com" in report
        assert remove_bookmark(loaded, 1)
        assert not remove_bookmark(loaded, 99)
        save(path, loaded)
        assert len(load(path)["bookmarks"]) == 1
    print("self-test OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Store bookmarks with tags, search them, and open them.",
        epilog="Exit codes: 0 success, 1 unavailable bookmark or storage error, "
        "2 usage error.",
    )
    ap.add_argument("--file", default=DEFAULT_FILE, help="bookmarks JSON file")
    ap.add_argument("--self-test", action="store_true", help="run built-in checks")
    sub = ap.add_subparsers(dest="command", metavar="command")

    add_parser = sub.add_parser("add", help="add a bookmark")
    add_parser.add_argument("url")
    add_parser.add_argument("-t", "--title", default="")
    add_parser.add_argument("--tags", action="append", default=[], metavar="TAG[,TAG]")

    list_parser = sub.add_parser("list", help="list bookmarks")
    list_parser.add_argument("--tag", metavar="TAG", help="only this tag")

    search_parser = sub.add_parser("search", help="search title, URL, and tags")
    search_parser.add_argument("query", nargs="+", metavar="TEXT")

    sub.add_parser("tags", help="list tags with counts")

    remove_parser = sub.add_parser("remove", help="delete by ID")
    remove_parser.add_argument("id", type=int)

    open_parser = sub.add_parser("open", help="open a bookmark in a browser")
    open_parser.add_argument("id", type=int)
    open_parser.add_argument("--print", dest="print_only", action="store_true",
                             help="print the URL instead of launching a browser")

    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.command:
        ap.print_help()
        return 2

    data = load(args.file)
    try:
        if args.command == "add":
            book = add_bookmark(data, args.url, args.title, args.tags)
            save(args.file, data)
            print(f"added #{book['id']}: {book['title']} <{book['url']}>")
        elif args.command == "list":
            show(find(data, "", args.tag))
        elif args.command == "search":
            query = " ".join(args.query)
            books = find(data, query)
            if not books:
                print(f"no bookmarks match: {query}")
                return 1
            show(books)
        elif args.command == "tags":
            counts = {}
            for book in data["bookmarks"]:
                for tag in book["tags"]:
                    counts[tag] = counts.get(tag, 0) + 1
            if not counts:
                print("no tags")
            for tag in sorted(counts):
                print(f"{tag:<20} {counts[tag]}")
        elif args.command == "remove":
            if not remove_bookmark(data, args.id):
                print(f"error: no bookmark with ID {args.id}", file=sys.stderr)
                return 1
            save(args.file, data)
            print(f"removed #{args.id}")
        elif args.command == "open":
            book = get_bookmark(data, args.id)
            if book is None:
                print(f"error: no bookmark with ID {args.id}", file=sys.stderr)
                return 1
            if args.print_only:
                print(book["url"])
            elif not webbrowser.open(book["url"]):
                print(f"could not launch a browser; URL: {book['url']}")
                return 1
            else:
                print(f"opened: {book['url']}")
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
