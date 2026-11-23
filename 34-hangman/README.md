# 34 - Hangman

Classic hangman against a built-in list of 35 lowercase words. Six wrong
letters draw the full ASCII gallows; guessing every letter wins. Repeated
guesses are rejected without costing a life, and invalid input is reported
without ending the game.

The word masking, wrong-letter tracking, win/lose state, and gallows stages are
all plain functions, so `--self-test` exercises them with no terminal.

## Run

```sh
python3 hangman.py
python3 hangman.py --seed 12
python3 hangman.py --self-test
python3 hangman.py --help
```

## Example

```text
  +---+
  |   |
  |   O
  |  /|\
  |  /
  |
=======

  word:  p y _ h _ n
  miss:  a e  (2/6)
letter>
```

Type one ASCII letter per turn. `q` quits early. Ctrl-D also exits cleanly.

## Exit codes

- `0` win, loss, quit, or successful self-test
- `2` invalid command-line options
