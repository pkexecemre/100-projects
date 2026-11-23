# 09-cron-explain

Translate a standard five-field cron expression into an English sentence, and
optionally list the next N run times. Fields are minute, hour, day of month,
month, day of week (Sunday is 0 or 7). Supports `*`, values, ranges, comma
lists, `/step` suffixes, three-letter month names (`JAN`..`DEC`) and weekday
names (`SUN`..`SAT`).

## Usage

```sh
./cron_explain.py '*/15 9-17 * * 1-5'
# Every 15 minutes past hours 9 through 17, Monday through Friday.

./cron_explain.py '30 2 * * *' --next 3
./cron_explain.py '0 0 1 * *' --next 2 --from '2024-01-15 12:00'
```

When both day-of-month and day-of-week are restricted, the standard cron OR rule
is used; otherwise both must match. `--next` scans minute by minute, starting
one minute after the reference time (default now), and gives up after five
years. If fewer runs than requested are found it exits 1 and says so on stderr.

## Exit codes

| code | meaning |
|------|---------|
| 0 | expression described successfully (and all requested runs found) |
| 1 | fewer than N next runs exist within the five-year window |
| 2 | malformed expression, bad `--from`, or invalid option |

## Test

`./cron_explain.py --self-test` checks field expansion (steps, ranges, names,
Sunday=7), rejects out-of-range and reversed expressions, verifies description
wording, and asserts known next-run dates for daily and Monday schedules.
