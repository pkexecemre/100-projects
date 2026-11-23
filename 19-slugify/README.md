# slugify

Turn arbitrary text into a URL-friendly slug. The default mode normalizes with
NFKD, removes accents, transliterates a few common letters (`ß`, `Æ`, `Ø`,
`Ł`, `Þ`, `Đ`), lowercases, and keeps only ASCII letters and digits. Emoji,
punctuation, and symbols are dropped or become separators.

## Usage

```sh
python3 slugify.py "Hello, World!"
# hello-world

python3 slugify.py "Héllo Wörld" --sep _
# hello_world

python3 slugify.py "你好 世界" --keep-unicode
# 你好-世界

printf 'Über Café' | python3 slugify.py
# uber-cafe
```

Options: `--sep STRING` (alias `--separator`, default `-`) and
`--keep-unicode` (preserve accented and non-Latin letters instead of
transliterating). Apostrophes are removed rather than turned into separators,
so `don't` becomes `dont`. Runs of separators collapse to one.

Input comes from the positional words or from stdin when no words are given.
Exit codes: `0` success, `2` for an empty separator or missing input.

## Test

```sh
python3 slugify.py --self-test
```

The offline test covers punctuation, accents, German ß, Æ/Ø transliteration,
apostrophes, custom separators, Unicode preservation, CJK text, and empty
results.
