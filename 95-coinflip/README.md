# 95-coinflip

Flip an arbitrary number of fair coins and report the sequence, totals,
percentages, the longest run of identical results, and a small ASCII
distribution bar. Seeded runs are fully reproducible.

## Usage

```sh
./coinflip.py                     # 20 flips
./coinflip.py -n 100 --seed 42    # reproducible run
./coinflip.py -n 5 --json         # JSON with flips and stats
./coinflip.py --self-test
```

The JSON object contains `count`, `seed`, `flips` (list of `"H"`/`"T"`),
`heads`, `tails`, `percentages`, and `longest_streak` (`side` and `length`).
Counts above 1,000,000 are rejected to keep memory bounded.

## Exit codes

- `0` success, including `--self-test`
- `1` bad flag or non-integer count (argparse)
- `2` count outside 1..1,000,000
