# 26-typing-test

A 30 second typing speed test with live words-per-minute and accuracy. Plain
HTML, CSS and JavaScript, no dependencies.

## Features

- Five built-in passages, chosen at random (and never the same twice in a row).
- The countdown starts on the first keystroke, not on the Start button.
- Character-by-character feedback: correct, incorrect, and current character.
- Live WPM, accuracy and seconds remaining while typing.
- Finishes at 30 seconds or earlier if the whole passage is typed.
- Paste and drag-drop are blocked so the score reflects typing.
- Start / Restart / Try again flow; responsive stats row.

## Calculation

WPM uses the standard five-characters-per-word convention:
`(correct characters / 5) / elapsed minutes`. Accuracy is
`correct characters / typed characters`. Only characters matching the passage
at the same position count as correct.

## Usage

Open `index.html`, or serve the folder:

```sh
cd 26-typing-test
python3 -m http.server 8000
```

Press Start test, then begin typing. Backspace works normally. Press Restart
for a fresh passage.

## Verification

```sh
python3 test.py
```

The smoke test checks required files and ids, the 30 second duration and WPM
logic markers, and that no web file references an external URL or calls
`fetch()`. Exit codes: 0 pass, 1 failed check, 2 bad command-line usage.
