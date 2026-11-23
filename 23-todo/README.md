# 23-todo

A small todo list that persists in the browser using `localStorage`. Plain
HTML, CSS and JavaScript with no dependencies.

## Features

- Add tasks with the form or Enter.
- Toggle tasks done with a custom checkbox; completed tasks are struck through.
- Delete individual tasks, or clear every completed task at once.
- Filter the list by All, Active or Done.
- Live count of remaining and total tasks.
- Storage errors (private mode, quota) are caught so the list still works for
  the current visit.
- Responsive paper-style card with a readable empty state.

## Usage

Open `index.html` directly, or serve the folder:

```sh
cd 23-todo
python3 -m http.server 8000
```

Tasks are saved under the key `things-to-do.v1`. Clearing site data for the
page removes the saved list.

## Verification

```sh
python3 test.py
```

The smoke test checks required files, ids for the form, input, list, filters
and count, plus the `localStorage` and filter logic markers. It also asserts no
web file references an external URL or calls `fetch()`. Exit codes: 0 pass,
1 failed check, 2 bad usage.
