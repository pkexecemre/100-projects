# 40 - Dice

A dice-notation parser, roller, and statistical simulator. Supports standard
`NdM` notation with modifiers, keep-highest/keep-lowest pools, and D&D-style
advantage/disadvantage.

## Notation

| Form | Meaning |
| --- | --- |
| `2d6+3` | roll two d6, add 3 |
| `d20` | one d20 |
| `1d8-2` | one d8, subtract 2 |
| `4d6kh3` | roll four d6, keep the highest three |
| `4d6kl2` | keep the lowest two |
| `2d20 advantage` | roll two d20, keep the highest (also `adv`) |
| `2d20 disadvantage` | keep the lowest (also `dis`) |

Limits: 1-100 dice, 2-1000 sides, modifier within +/-10000, kept count from
1 to the dice count. Advantage forces at least two dice and keeps one. Mixing
`advantage` with `kh`/`kl` is rejected.

## Run

```sh
python3 dice.py 2d6+3
python3 dice.py "4d6kh3"
python3 dice.py 2d20 advantage --seed 4
python3 dice.py 3d6 --times 5
python3 dice.py 2d6+3 --stats 10000
python3 dice.py                      # interactive prompt
python3 dice.py --self-test
python3 dice.py --help
```

The interactive prompt accepts one expression per line and prints each roll;
`q` or Ctrl-D exits. Bad notation prints an error and does not exit.

## Exit codes

- `0` roll/stats completed, interactive quit, or successful self-test
- `1` invalid dice notation on the command line
- `2` invalid options (`--times`, `--stats`, missing notation)
