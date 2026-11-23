# 96-lottery

Pick unique lottery numbers from any inclusive numeric range. You control the
range (`--min`/`--max`), how many numbers per ticket (`--count`), how many
tickets to draw (`--sets`), and reproducibility (`--seed`). Tickets are sorted
by default; `--no-sort` preserves the random draw order.

## Usage

```sh
./lottery.py                          # 6 numbers from 1-49
./lottery.py --min 1 --max 59 --count 6 --sets 3
./lottery.py --min 10 --max 20 --count 3 --seed 7 --json
./lottery.py --no-sort --seed 1
./lottery.py --self-test
```

Numbers within one ticket are always unique. Different tickets may share
numbers. `--count` cannot exceed the size of the range. At most 100 tickets are
drawn per invocation.

## Exit codes

- `0` success, including `--self-test`
- `1` bad flag or non-integer argument (argparse)
- `2` invalid range, impossible count, or set count outside 1..100
