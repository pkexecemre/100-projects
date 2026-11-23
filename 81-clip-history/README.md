# 81 - clip-history

Keep a small, deduplicated history of clipboard text. `snapshot` reads the
current clipboard through `wl-paste` (Wayland) when available and falls back to
`xclip` (X11). If neither tool exists, or the clipboard cannot be read, the
command fails with a clear message instead of crashing.

## Usage

```sh
python3 clip_history.py snapshot       # store clipboard text
python3 clip_history.py list           # newest first
python3 clip_history.py list -n 5      # show five entries
python3 clip_history.py search invoice # case-insensitive search
python3 clip_history.py clear          # remove the history file
python3 clip_history.py --self-test
```

Entries are one text blob each. Storing a blob that is already anywhere in the
history moves it to the newest position, so no duplicates accumulate. Repeated
snapshots of the same newest blob are reported as a duplicate. The default
store is `clip-history.json` next to the script; use `--file PATH` to choose
another location. Newlines and tabs are flattened when a preview is printed.

## Exit codes

- `0` success, including a duplicate snapshot or clearing an empty history
- `1` clipboard unavailable/empty, unreadable store, or no search matches
- `2` usage error (no command, bad option value)

Run the built-in checks with `--self-test`; it exercises storage, deduplication,
preview formatting, and discovery without needing a clipboard.
