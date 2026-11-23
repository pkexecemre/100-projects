# 29-reaction-test

A five-attempt reaction timer with a random wait. The panel turns green after
1.4 to 4 seconds; click as soon as it does. Plain HTML, CSS and JavaScript.

## Features

- Random delay on every attempt so you cannot anticipate the green.
- Clicking early cancels the attempt with a "Too soon" message; it is not
  counted.
- Tracks last, best and average time in milliseconds across five attempts.
- Attempt counter shows progress (`3 / 5`).
- Round ends after five valid attempts; Reset stats clears everything.
- Keyboard-friendly: the arena is a button, so Space or Enter activates it.
- Responsive panel and two-by-two stats grid on small screens.

## Usage

Open `index.html`, or serve the folder:

```sh
cd 29-reaction-test
python3 -m http.server 8000
```

Press Start. The panel shows a warning colour and then turns green. Click it
once. After a result, press Start (or click the panel) for the next attempt.
Times are measured with `performance.now()`.

## Verification

```sh
python3 test.py
```

The smoke test checks required files, arena/start/stats ids, the five-attempt
limit and timing markers, and that no web file references an external URL or
calls `fetch()`. Exit codes: 0 pass, 1 failed check, 2 bad usage.
