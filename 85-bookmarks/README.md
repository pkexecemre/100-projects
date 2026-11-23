# 85 - bookmarks

A small JSON bookmark manager. Bookmarks have an ID, URL, title, tag list, and
an added date. You can add, list, filter by tag, search title/URL/tags, see tag
counts, remove, and open a bookmark in the default browser.

## Usage

```sh
python3 bookmarks.py add https://docs.python.org -t "Python docs" --tags python,docs
python3 bookmarks.py add https://example.com --tags misc
python3 bookmarks.py list
python3 bookmarks.py list --tag python
python3 bookmarks.py search docs
python3 bookmarks.py tags
python3 bookmarks.py open 1          # launches the default browser
python3 bookmarks.py open 1 --print  # prints the URL only
python3 bookmarks.py remove 2
python3 bookmarks.py --self-test
```

`add` accepts only `http://` and `https://` URLs and rejects duplicates. Tags
are lowercase, comma-separated, and deduplicated. Search is case-insensitive
across the title, URL, and tags. `open` attempts `webbrowser.open`; on a headless
machine use `--print` or the command reports that no browser was launched.

The store defaults to `bookmarks.json` next to the script; `--file PATH`
overrides it. New IDs are one above the current highest ID.

## Exit codes

- `0` success
- `1` no matching bookmark, duplicate/invalid URL, failed browser launch
- `2` usage error

`--self-test` checks add, tag cleaning, search, duplicate rejection, listing,
removal, missing IDs, and round-trip persistence using a temporary file.
