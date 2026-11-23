# 27-countdown

A live event countdown with a date-time picker. Set a name and a future moment
and see days, hours, minutes and seconds until it arrives. Plain HTML, CSS and
JavaScript.

## Features

- Event name and `datetime-local` picker with a future-date check.
- Countdown refreshes four times a second and shows days / hours / minutes /
  seconds.
- The most recent event is stored in `localStorage` and restored on reload.
- Zeroes out and reports "has arrived" once the target passes.
- Tab title shows the remaining time.
- Responsive board: four columns become a two-by-two grid on phones.

## Usage

Open `index.html`, or serve the directory:

```sh
cd 27-countdown
python3 -m http.server 8000
```

The first visit counts down to the next New Year in local time. Change the name
or date and press Set countdown. Times are interpreted in the browser's local
time zone.

## Verification

```sh
python3 test.py
```

The smoke test checks required files, all display ids, the date picker, and
storage/interval markers. It also asserts no web file references an external
URL or calls `fetch()`. Exit codes: 0 pass, 1 failed check, 2 bad usage.
