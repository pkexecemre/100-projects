# 90 - workout-log

A JSON strength-training log. Record an exercise with sets, reps per set, and
weight, then get weekly volume broken down by exercise. Volume is
`sets * reps * weight`, and weeks run Monday through Sunday.

## Usage

```sh
python3 workout_log.py log squat --sets 5 --reps 5 --weight 100
python3 workout_log.py log bench --sets 3 --reps 8 --weight 60 --date 2026-11-25
python3 workout_log.py list
python3 workout_log.py list -n 20
python3 workout_log.py stats
python3 workout_log.py stats --week 2026-11-23
python3 workout_log.py --self-test
```

`--sets` defaults to 1, while `--reps` and `--weight` are required. Weight may
be 0 for bodyweight work and is stored to two decimals. `stats` prints sets,
total reps, and volume per exercise for the week containing `--week` (default:
today), plus a grand total. `list` shows the newest entries first.

The store defaults to `workouts.json` next to the script; `--file PATH` points
to another file. Invalid records already in the file are skipped on load.

## Exit codes

- `0` success
- `1` storage failure or empty exercise name
- `2` usage error (bad date, non-positive sets/reps, negative weight, missing command)

`--self-test` checks Monday-week boundaries, volume math, per-exercise
aggregation (including two sessions of one lift), totals, the recent list,
empty-week output, and input validation.
