# 36 - Tic-Tac-Toe

Tic-tac-toe with two modes: play against a perfect minimax AI (default) or
against a second player on the same terminal. The board shows numbered empty
cells; enter the number to claim it.

The AI scores terminal positions with depth preference (win sooner, lose
later), so it takes an immediate win and blocks an immediate loss. Because
tic-tac-toe is a draw with perfect play, the AI can never be beaten.

## Run

```sh
python3 tic_tac_toe.py              # human X vs AI O
python3 tic_tac_toe.py --mode 2p    # two local players
python3 tic_tac_toe.py --self-test  # rule and AI checks
python3 tic_tac_toe.py --help
```

## Board input

Cells are numbered like a keypad:

```text
 1 | 2 | 3
---+---+---
 4 | 5 | 6
---+---+---
 7 | 8 | 9
```

`q` or Ctrl-D quits. Taken cells and out-of-range numbers are rejected without
using a turn.

The self-test also plays 120 seeded games with a random human opponent and
asserts the AI never loses.

## Exit codes

- `0` win, loss, draw, quit, or successful self-test
- `2` invalid `--mode` or other command-line options
