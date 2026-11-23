# 37 - Guess the Number

Two-way number guessing with binary-search bookkeeping.

Default mode picks a secret in `1..--max` and lets you guess. After each miss
it tells you higher or lower and narrows the feasible range on screen. At the
end it reports your guess count next to the optimal worst case
`ceil(log2(max+1))`.

`--computer` reverses the game: you think of a number and answer `c` / `h` / `l`
while the program halves the range. It detects contradictory answers and exits
1.

## Run

```sh
python3 guess_number.py
python3 guess_number.py --max 1000 --seed 7
python3 guess_number.py --computer --max 500
python3 guess_number.py --self-test
python3 guess_number.py --help
```

## Example

```text
I picked a number from 1 to 100.
Binary search needs at most 7 guesses.

guess (1-100, q)> 50
50 is too low - go higher.
Range is now 51-100.
```

`q` or Ctrl-D quits. Non-numeric and out-of-range guesses do not count as
attempts.

## Exit codes

- `0` guessed correctly, computer found your number, quit, or self-test passed
- `1` contradictory answers in computer mode
- `2` invalid command-line options
