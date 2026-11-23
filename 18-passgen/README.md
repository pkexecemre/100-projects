# passgen

Generate secure random passwords with Python's `secrets` module. Character
classes are selectable, and at least one character from every enabled class is
guaranteed to appear. The pool is shuffled with a cryptographically secure
Fisher-Yates pass.

## Usage

```sh
python3 passgen.py
python3 passgen.py --length 24 --count 5
python3 passgen.py --length 20 --no-symbols --exclude-ambiguous
python3 passgen.py --length 16 --entropy
python3 passgen.py --length 16 --count 2 --json
```

Options: `--length N` (default 16), `--count N` (default 1), `--no-upper`,
`--no-lower`, `--no-digits`, `--no-symbols`, `--symbols CHARS`,
`--exclude-ambiguous` (drops `I l 1 O 0 o |` and quotes), and `--entropy`.
`--entropy` writes the pool entropy to stderr and keeps stdout clean; `--json`
reports the same value as `entropy_bits`.

Entropy is computed as `length * log2(pool size)`, an upper bound that ignores
the class-presence constraints. Default settings (16 chars, 86-character pool)
give about 103 bits.

Exit codes: `0` success, `2` when no classes are enabled, when the length is
shorter than the number of enabled classes, or on bad arguments.

## Test

```sh
python3 passgen.py --self-test
```

The self-test checks class guarantees, uniqueness, length, entropy math,
ambiguous-character removal, and rejection of impossible lengths.
