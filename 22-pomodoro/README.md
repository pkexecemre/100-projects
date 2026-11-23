# 22-pomodoro

A single-card Pomodoro timer built with plain HTML, CSS and JavaScript. No
dependencies, no build step, no network calls.

## Features

- 25 minute focus phase and 5 minute break phase.
- Start, Pause and Reset controls, plus Space as a start/pause shortcut.
- SVG progress ring that drains with the remaining time.
- Session counter increments after every completed focus phase.
- Automatic phase switch at zero with a short Web Audio chime.
- Tab title mirrors the remaining time and current phase.

## Usage

Open `index.html` in a browser, or serve the directory:

```sh
cd 22-pomodoro
python3 -m http.server 8000
```

Press Start. The break is queued when focus ends; press Start again to run the
break. Reset returns to a fresh 25:00 focus session and keeps the session count.
Reloading the page clears the in-memory session count.

## Verification

```sh
python3 test.py
```

The smoke test checks required files, element ids, timer constants, and that no
web file references an external URL or uses `fetch()`. Exit codes: 0 success,
1 a check failed, 2 bad command-line usage (argparse).
