# 53 - cron-line

Validate a cron schedule and a command, then print a ready-to-paste crontab
line together with comments explaining when it runs and the next occurrences.
Python 3 standard library only.

## Usage

```sh
./cron_line.py "*/15 9-17 * * mon-fri" /usr/bin/logger "hourly-ish tick"
./cron_line.py --name backup "@daily" /usr/bin/restic backup /srv
./cron_line.py "@reboot" /usr/bin/boot-task
```

Output:

```text
# job: backup
# runs daily at 00:00
# next: 2026-11-24 00:00, 2026-11-25 00:00, 2026-11-26 00:00
0 0 * * * /usr/bin/restic backup /srv```

Schedules may be standard five-field expressions or the macros `@reboot`,
`@yearly`, `@annually`, `@monthly`, `@weekly`, `@daily`, `@midnight`, and
`@hourly`. Fields accept `*`, numbers, names (`jan`, `mon`), ranges (`9-17`),
lists (`1,15,30`), and steps (`*/5`, `0-30/10`). Day-of-month and day-of-week
follow cron's OR rule when both are restricted.

The command must be a single line. An unescaped `%` is rejected because cron
turns it into a newline; write `\%` for a literal percent. Words that are not
recognised as options of this tool become the command, so quote the schedule.
Put `--name` before the schedule or command. Insert `--` before the command if
it contains options that clash with this tool's (`-h`, `--name`); it is
removed before the crontab line is built. A note is added when the program path
is relative, because cron runs with a minimal `PATH`.

## Exit codes

- `0` - schedule and command are valid; line printed
- `2` - invalid schedule, empty or multi-line command, unescaped percent

## Test

```sh
./cron_line.py --self-test
```

Checks field expansion, name and range parsing, macro handling, rejection of
out-of-range and malformed schedules, percent/newline command rejection, and
next-run calculation from a fixed start time.
