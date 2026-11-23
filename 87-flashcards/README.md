# 87 - flashcards

A JSON flashcard deck with an interactive quiz. Each card stores its answer,
how many times it was answered correctly, and how many times it was missed.
Quiz scores accumulate in the deck file.

## Usage

```sh
python3 flashcards.py add "Capital of France?" "Paris"
python3 flashcards.py add "H2O" "water|dihydrogen monoxide"
python3 flashcards.py list
python3 flashcards.py quiz
python3 flashcards.py quiz --limit 5 --no-shuffle
python3 flashcards.py --self-test
```

Grading is deliberately forgiving: the comparison is case-insensitive, collapses
whitespace, strips surrounding punctuation, and accepts alternatives separated
by `|` in the stored answer. A blank answer counts as wrong. Type an answer at
the prompt; Ctrl-D ends the quiz early and still reports the cards answered so
far. Add `--limit N` to cap a session and `--no-shuffle` to preserve deck order.

The deck defaults to `deck.json` next to the script; `--file PATH` overrides it.
Duplicate questions (case-insensitive) are rejected.

## Exit codes

- `0` success, including a partially completed quiz
- `1` empty deck, duplicate/empty card, or storage failure
- `2` usage error

`--self-test` covers answer normalization and alternative matching, duplicate
rejection, persistence, and a scripted two-card quiz checking the score and
per-card counters.
