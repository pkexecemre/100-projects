# 89 - meal-plan

A weekly meal planner stored as JSON. Each day has four optional slots:
breakfast, lunch, dinner, and snack. `show` prints Monday through Sunday with
dates and marks today.

## Usage

```sh
python3 meal_plan.py add mon dinner Pasta
python3 meal_plan.py add wed lunch "Lentil soup"
python3 meal_plan.py add fri dinner "Homemade pizza" --week 2026-11-23
python3 meal_plan.py show
python3 meal_plan.py show --week 2026-12-07
python3 meal_plan.py remove wed lunch
python3 meal_plan.py --self-test
```

Days may be short names (`mon`..`sun`), full names, or explicit
`YYYY-MM-DD` dates. Short and full names are resolved within the week
containing `--week` (default: today's week, starting Monday). Slots are
validated, and adding the same slot again replaces the dish. Removing an empty
slot returns an error and exit code `1`.

The store defaults to `meal-plan.json` next to the script; `--file PATH`
selects another file. Empty slots display as `-`.

## Exit codes

- `0` success
- `1` unknown day/slot, empty dish, nothing to remove, or storage failure
- `2` usage error (bad date or missing command)

`--self-test` verifies Monday-week math (including Sunday), weekday and full
name resolution, ISO dates, slot validation, set/remove behavior, the week
view, and persistence.
