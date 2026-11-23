# 83 - habit-log

A JSON-backed daily habit tracker. Each `--add NAME` records today's date for
that habit, and `--stats` prints the current streak, best streak, total days,
and check-ins in the last seven days.

## Usage

```sh
python3 habit_log.py --add reading
python3 habit_log.py --add exercise --stats
python3 habit_log.py --stats
python3 habit_log.py --file ~/habits.json --add water
python3 habit_log.py --self-test
```

Data is stored as `{"habits": {"name": ["YYYY-MM-DD", ...]}}` in `habits.json`
next to the script by default. Checking in twice on the same day is harmless:
it reports the duplicate and changes nothing. A current streak counts back from
today; if today has not been logged yet, a streak that ended yesterday stays
alive. Longest streak is computed across all recorded days.

Output is a fixed-width table, for example:

```
habit    streak  best  total  last7
reading       3     7     42      5
```

## Exit codes

- `0` success (including a duplicate check-in)
- `1` empty habit name or unreadable/corrupt store
- `2` no action requested or a bad option

`--self-test` uses a temporary file with fixed dates to verify streak math,
gaps, duplicate suppression, persistence, and the stats table.
