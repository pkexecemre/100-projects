# line-diff

Compare two text files line by line using a longest-common-subsequence table.
Unchanged lines are prefixed with a space, removed lines with `-`, and added
lines with `+`. Only the changed lines of each side are shown, in order.

## Usage

```sh
python3 line_diff.py old.txt new.txt
python3 line_diff.py old.txt new.txt --stat
python3 line_diff.py - new.txt < old.txt
```

Example:

```
  unchanged
- old line
+ new line
```

`--stat` prints only `N additions, M deletions`. One input may be `-` to read
it from stdin. Inputs are decoded as UTF-8. Very large inputs (more than 16
million LCS cells) are rejected with an error rather than exhausting memory.

Exit codes:

- `0` files are identical
- `1` files differ (also with `--stat`)
- `2` unreadable file, invalid input, or oversized comparison

## Test

```sh
python3 line_diff.py --self-test
```

The self-test exercises pure additions, deletions, replacements, identical
files, CLI exit codes, and `--stat` output.
