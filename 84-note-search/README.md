# 84 - note-search

Recursive grep for a directory of notes. Searches every UTF-8 text file, skips
hidden directories, common VCS/build folders, binary files, and files over 2 MB.
Matches are printed in grep format with configurable context and optional
color highlighting.

## Usage

```sh
python3 note_search.py invoice ~/notes
python3 note_search.py -C 3 --case-sensitive "API key" ./notes
python3 note_search.py "meeting|agenda" notes --color always
python3 note_search.py -m 20 error notes
python3 note_search.py --self-test
```

Matching is case-insensitive by default (pass `-s` to change that) and uses
Python regular expressions. Match lines look like `file:12:text`; context lines
look like `file-11-text`. Non-adjacent context groups are separated by `--`.
If the match limit is reached, a notice is written to stderr and the exit code
is still `0` because matches were found.

## Exit codes

- `0` at least one match
- `1` no matches
- `2` bad pattern, missing directory, or usage error

The self-test creates a temporary notes tree and checks recursive traversal,
case sensitivity, context output, ANSI highlighting, the match limit, empty
results, and invalid-pattern handling.
