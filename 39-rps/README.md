# 39 - Rock Paper Scissors

Best-of-N rock-paper-scissors against a random computer. The first side to
`floor(N/2) + 1` round wins takes the series; ties are replayed and tracked
separately. Default is best of 3.

`winner`, `parse_move`, and `series_over` are pure functions, including a
seeded full-series simulation in the self-test.

## Run

```sh
python3 rps.py
python3 rps.py --best-of 5 --seed 8
python3 rps.py --self-test
python3 rps.py --help
```

## Play

Enter `rock`, `paper`, `scissors`, or the single letters `r`, `p`, `s`.
Invalid words are rejected without consuming a round, and `q` or Ctrl-D quits
immediately.

```text
Best of 3 - first to 2 wins. Ties do not count.

your move> r
you: rock     computer: scissors you win
score  you 1 - 0 computer   ties 0
```

## Exit codes

- `0` series finished, quit, or successful self-test
- `2` even/out-of-range `--best-of` or other invalid options
