# 92-quotes

A tiny quote machine with the collection embedded in the script, so it works
completely offline. Quotes carry tags (`tech`, `wisdom`, `life`, `courage`,
`humor`); you can filter by tag, list everything, or ask for JSON.

## Usage

```sh
./quotes.py                        # random quote
./quotes.py --tag tech             # random tech quote
./quotes.py --tag tech --seed 7    # reproducible pick
./quotes.py --list                 # numbered list of all quotes
./quotes.py --list-tags            # tags and counts
./quotes.py --json                 # JSON object
./quotes.py --self-test
```

A single unknown tag fails with exit code 2 and the list of valid tags on
stderr. `--seed` makes repeated picks reproducible when the quote pool is the
same.

## Exit codes

- `0` success, including `--list`, `--list-tags` and `--self-test`
- `2` unknown tag
