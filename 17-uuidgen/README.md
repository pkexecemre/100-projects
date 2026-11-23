# uuidgen

Generate random UUID version 4 values in bulk using Python's `uuid` module.
Output is one UUID per line, lower-case with hyphens by default.

## Usage

```sh
python3 uuidgen.py
python3 uuidgen.py --count 5
python3 uuidgen.py --count 3 --prefix user_ --upper
python3 uuidgen.py --count 1 --suffix .json --no-dashes
```

Options: `--count N` (1 to 1,000,000, default 1), `--prefix TEXT`,
`--suffix TEXT`, `--upper`, and `--no-dashes`. Prefix and suffix are applied
around every generated value.

Example output:

```
f47ac10b-58cc-4372-a567-0e02b2c3d479
```

Exit codes: `0` success, `2` for an out-of-range count or bad arguments.

## Test

```sh
python3 uuidgen.py --self-test
```

The self-test generates 100 values, checks uniqueness, version/variant bits,
format, prefix/suffix handling, uppercase mode, and dash removal.
