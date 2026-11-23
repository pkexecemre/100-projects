# 91-blocktext

Render uppercase A-Z, digits 0-9 and spaces as big 5x7 block letters made of
`#` characters. Every command-line argument becomes its own rendered line, so
multi-line output is just multiple arguments. Lowercase input is folded to
uppercase; unsupported characters are rejected with a clear message.

## Usage

```sh
./blocktext.py HELLO
./blocktext.py AB 12
printf 'OK\n42\n' | ./blocktext.py
./blocktext.py --self-test
```

Each line is seven rows tall; glyphs are separated by one blank column. Lines
are separated by one blank row.

## Exit codes

- `0` success (also `--self-test` when all checks pass)
- `1` argument parser errors (missing input, bad flag)
- `2` unsupported character in the input
