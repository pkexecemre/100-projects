# 88 - reading-list

A JSON reading list with three statuses (`want`, `reading`, `read`) and a 0-5
star rating. Books can be added, listed (optionally by status), updated, and
removed.

## Usage

```sh
python3 reading_list.py add "Dune" --author "Frank Herbert" --status reading
python3 reading_list.py add "Neuromancer" --author "William Gibson"
python3 reading_list.py list
python3 reading_list.py list --status want
python3 reading_list.py update 2 --status read --rating 4
python3 reading_list.py remove 1
python3 reading_list.py --self-test
```

Status aliases `to-read`/`todo` map to `want`, `current` maps to `reading`, and
`done`/`finished` map to `read`. A rating of `0` means unrated and displays as
`-`; `--rating 0` on update clears a rating. Lists are grouped by status
(want, then reading, then read) and sorted by ID inside each group.

The store defaults to `reading-list.json` next to the script; use `--file PATH`
to point at another file.

## Exit codes

- `0` success
- `1` unknown book ID, invalid update with no fields, or storage failure
- `2` usage error (bad status or rating, no command)

`--self-test` exercises add/update/remove, status filtering, star output,
missing IDs, and JSON persistence. It also verifies the status and rating
parsers.
